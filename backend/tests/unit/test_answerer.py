import uuid

import pytest

from app.generation.answerer import (
    AbstainGate,
    AbstainReason,
    AnswerConfig,
    AnswerService,
    AnswerStatus,
    DoneEvent,
    ReplaceEvent,
    RetrievalEvent,
    TokenEvent,
)
from app.generation.llm import ChatMessage, LLMUnavailableError
from app.generation.prompts import ABSTAIN_TOKEN, NO_ANSWER_MESSAGE
from app.retrieval.retriever import HybridRetriever, RetrievalConfig
from app.retrieval.store import ChunkRecord, InMemoryChunkStore
from tests.fakes import HashingEmbedder, OverlapReranker, ScriptedLLM

PASSAGES = [
    ("Leave Policy", "Entitlement", "Full-time employees receive 25 days of paid annual leave."),
    ("Leave Policy", "Carry-Over", "Employees may carry over up to 5 unused leave days."),
    ("Travel Policy", "Hotels", "Hotels are reimbursed up to 200 per night."),
]


def build_service(llm: ScriptedLLM, coverage: float = 1.0) -> AnswerService:
    document_id = uuid.uuid4()
    records = [
        ChunkRecord(uuid.uuid4(), document_id, title, heading, None, text)
        for title, heading, text in PASSAGES
    ]
    embedder = HashingEmbedder()
    store = InMemoryChunkStore(
        records, embedder.embed_documents([record.contextual_text for record in records])
    )
    retriever = HybridRetriever(
        store, embedder, OverlapReranker(), RetrievalConfig(top_k=2, min_relevance=0.3)
    )
    config = AnswerConfig("answer-model", "rewrite-model", min_citation_coverage=coverage)
    return AnswerService(retriever, llm, config)


def run(service: AnswerService, question: str, history: list[ChatMessage] | None = None) -> list:
    return list(service.stream(question, history or []))


def test_cited_answer_is_streamed_and_accepted() -> None:
    llm = ScriptedLLM(answers=["Full-time employees receive 25 days of paid annual leave [1]."])
    events = run(build_service(llm), "How many days of annual leave do employees receive?")

    assert isinstance(events[0], RetrievalEvent)
    assert events[0].documents == ["Leave Policy"]
    streamed = "".join(event.text for event in events if isinstance(event, TokenEvent))
    assert streamed == "Full-time employees receive 25 days of paid annual leave [1]."

    answer = events[-1].answer
    assert answer.status is AnswerStatus.ANSWERED
    assert [citation.heading for citation in answer.citations] == ["Entitlement"]
    assert answer.citation_coverage == 1.0
    assert not answer.repaired
    assert [call.stage for call in answer.llm_calls] == ["generate"]
    span_names = [span["name"] for span in answer.trace["spans"]]
    assert span_names[-1] == "generate"


def test_question_without_sources_abstains_without_calling_the_model() -> None:
    llm = ScriptedLLM()
    answer = build_service(llm).answer("Where can I park a motorbike?")
    assert answer.status is AnswerStatus.ABSTAINED
    assert answer.abstain_reason is AbstainReason.NO_RELEVANT_SOURCES
    assert answer.text == NO_ANSWER_MESSAGE
    assert llm.calls == []


def test_model_abstention_is_never_streamed() -> None:
    llm = ScriptedLLM(answers=[ABSTAIN_TOKEN])
    events = run(build_service(llm), "Do annual leave days expire?")
    assert not [event for event in events if isinstance(event, TokenEvent | ReplaceEvent)]
    answer = events[-1].answer
    assert answer.status is AnswerStatus.ABSTAINED
    assert answer.abstain_reason is AbstainReason.MODEL_DECLINED


def test_invalid_citations_are_repaired() -> None:
    llm = ScriptedLLM(
        answers=["Employees receive 25 days of paid annual leave [7]."],
        completions=["Employees receive 25 days of paid annual leave [1]."],
    )
    events = run(build_service(llm), "How many days of annual leave do employees receive?")
    replace = [event for event in events if isinstance(event, ReplaceEvent)]
    assert replace[0].text == "Employees receive 25 days of paid annual leave [1]."

    answer = events[-1].answer
    assert answer.status is AnswerStatus.ANSWERED
    assert answer.repaired
    assert [call.stage for call in answer.llm_calls] == ["generate", "repair"]
    repair_prompt = llm.calls[1][1][-1]["content"]
    assert "cites sources that do not exist (7)" in repair_prompt


def test_answer_is_withheld_when_repair_still_fails() -> None:
    llm = ScriptedLLM(
        answers=["Employees receive twenty five days of paid annual leave."],
        completions=["Employees still receive twenty five days of annual leave each year."],
    )
    events = run(build_service(llm), "How many days of annual leave do employees receive?")
    assert events[-2] == ReplaceEvent(NO_ANSWER_MESSAGE)
    answer = events[-1].answer
    assert answer.status is AnswerStatus.ABSTAINED
    assert answer.abstain_reason is AbstainReason.CITATIONS_INVALID
    assert answer.citations == []


def test_follow_up_questions_are_rewritten_before_retrieval() -> None:
    llm = ScriptedLLM(
        completions=["How many unused leave days can employees carry over?"],
        answers=["Employees may carry over up to 5 unused leave days [1]."],
    )
    history: list[ChatMessage] = [
        {"role": "user", "content": "How much annual leave do I get?"},
        {"role": "assistant", "content": "You receive 25 days [1]."},
    ]
    answer = build_service(llm).answer("And how many can I carry over?", history)
    assert answer.standalone_question == "How many unused leave days can employees carry over?"
    assert answer.citations[0].heading == "Carry-Over"
    assert [call.stage for call in answer.llm_calls] == ["rewrite", "generate"]


def test_rewrite_failure_falls_back_to_the_original_question() -> None:
    llm = ScriptedLLM()
    llm.failure = LLMUnavailableError("down", reason="network")
    history: list[ChatMessage] = [{"role": "user", "content": "Hello"}]
    with pytest.raises(LLMUnavailableError):
        build_service(llm).answer("How many days of annual leave do employees receive?", history)
    assert llm.calls[0][0] == "complete"
    assert llm.calls[1][0] == "stream"


def test_gate_holds_back_only_while_output_could_be_the_abstain_token() -> None:
    gate = AbstainGate(ABSTAIN_TOKEN)
    assert gate.feed("I") == ""
    assert gate.feed("NS") == ""
    assert gate.feed("URE") == "INSURE"
    assert gate.feed(" more") == " more"

    suppressed = AbstainGate(ABSTAIN_TOKEN)
    assert suppressed.feed("INSUFFICIENT_") == ""
    assert suppressed.feed("CONTEXT") == ""
    assert suppressed.release() == ""
    assert suppressed.suppressed


def test_done_event_is_always_last() -> None:
    llm = ScriptedLLM(answers=["Hotels are reimbursed up to 200 per night [1]."])
    events = run(build_service(llm), "What is the hotel limit per night?")
    assert isinstance(events[-1], DoneEvent)
