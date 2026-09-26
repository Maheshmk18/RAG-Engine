import logging
import re
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from app.generation.citations import CitationReport, check_citations, normalize_citations
from app.generation.llm import ChatMessage, Completion, LLMClient, LLMUnavailableError
from app.generation.prompts import (
    ABSTAIN_TOKEN,
    NO_ANSWER_MESSAGE,
    answer_messages,
    repair_messages,
    rewrite_messages,
)
from app.retrieval.retriever import HybridRetriever, Passage
from app.telemetry.tracing import Trace

logger = logging.getLogger(__name__)


class AnswerStatus(StrEnum):
    ANSWERED = "answered"
    ABSTAINED = "abstained"


class AbstainReason(StrEnum):
    NO_RELEVANT_SOURCES = "no_relevant_sources"
    MODEL_DECLINED = "model_declined"
    CITATIONS_INVALID = "citations_invalid"


@dataclass(frozen=True)
class AnswerConfig:
    answer_model: str
    rewrite_model: str
    temperature: float = 0.1
    max_tokens: int = 800
    min_citation_coverage: float = 0.8
    history_messages: int = 6


@dataclass(frozen=True)
class Citation:
    number: int
    chunk_id: str
    document_id: str
    document_title: str
    heading: str | None
    page: int | None
    text: str
    relevance: float

    @classmethod
    def from_passage(cls, number: int, passage: Passage) -> "Citation":
        chunk = passage.chunk
        return cls(
            number=number,
            chunk_id=chunk.id,
            document_id=chunk.document_id,
            document_title=chunk.document_title,
            heading=chunk.heading,
            page=chunk.page,
            text=chunk.text,
            relevance=passage.relevance,
        )


@dataclass(frozen=True)
class LLMCall:
    stage: str
    model: str
    prompt_tokens: int
    completion_tokens: int

    @classmethod
    def from_completion(cls, stage: str, completion: Completion) -> "LLMCall":
        return cls(
            stage,
            completion.model,
            completion.usage.prompt_tokens,
            completion.usage.completion_tokens,
        )


@dataclass
class Answer:
    text: str
    status: AnswerStatus
    standalone_question: str
    citations: list[Citation] = field(default_factory=list)
    passages: list[Passage] = field(default_factory=list)
    abstain_reason: AbstainReason | None = None
    citation_coverage: float | None = None
    repaired: bool = False
    llm_calls: list[LLMCall] = field(default_factory=list)
    trace: dict[str, Any] = field(default_factory=dict)

    def metrics(self) -> dict[str, Any]:
        return {
            "standalone_question": self.standalone_question,
            "abstain_reason": self.abstain_reason,
            "citation_coverage": self.citation_coverage,
            "repaired": self.repaired,
            "passages": len(self.passages),
            "llm_calls": [vars(call) for call in self.llm_calls],
            "trace": self.trace,
        }


@dataclass(frozen=True)
class RetrievalEvent:
    documents: list[str]
    passages: int


@dataclass(frozen=True)
class TokenEvent:
    text: str


@dataclass(frozen=True)
class ReplaceEvent:
    text: str


@dataclass(frozen=True)
class DoneEvent:
    answer: Answer


AnswerEvent = RetrievalEvent | TokenEvent | ReplaceEvent | DoneEvent


class AbstainGate:
    def __init__(self, token: str) -> None:
        self.token = token
        self.buffer = ""
        self.released = False
        self.suppressed = False

    def feed(self, delta: str) -> str:
        if self.released:
            return delta
        self.buffer += delta
        pending = self.buffer.lstrip()
        if pending.startswith(self.token):
            self.suppressed = True
            return ""
        if self.suppressed or self.token.startswith(pending):
            return ""
        return self.release()

    def release(self) -> str:
        if self.suppressed or self.released:
            return ""
        self.released = True
        text, self.buffer = self.buffer, ""
        return text


def is_abstention(text: str) -> bool:
    stripped = text.strip()
    return not stripped or stripped.startswith(ABSTAIN_TOKEN)


def unique_titles(passages: Sequence[Passage]) -> list[str]:
    return list(dict.fromkeys(passage.chunk.document_title for passage in passages))


GREETING_QUESTIONS = {
    "hi",
    "hi there",
    "hello",
    "hello there",
    "hey",
    "hey there",
    "good morning",
    "good afternoon",
    "good evening",
}
WELLBEING_QUESTIONS = {"how are you", "how are you doing", "how are you today"}
DOCUMENT_COUNT_QUESTION = re.compile(r"\bhow many\s+(?:documents?|docs?|files?|policies?)\b")
DOCUMENT_COUNT_SCOPE = re.compile(
    r"\b(?:do you have|you have|do we have|we have|are there|are indexed|are uploaded|"
    r"have you uploaded|indexed|uploaded|available|in (?:your|the) "
    r"(?:knowledge base|repository|database|corpus))\b"
)


class AnswerService:
    def __init__(self, retriever: HybridRetriever, llm: LLMClient, config: AnswerConfig) -> None:
        self.retriever = retriever
        self.llm = llm
        self.config = config

    def answer(self, question: str, history: Sequence[ChatMessage] = ()) -> Answer:
        for event in self.stream(question, history):
            if isinstance(event, DoneEvent):
                return event.answer
        raise RuntimeError("The answer stream ended without a result")

    def stream(self, question: str, history: Sequence[ChatMessage] = ()) -> Iterator[AnswerEvent]:
        trace = Trace()
        if quick_answer := self.quick_answer(question, trace):
            yield RetrievalEvent(documents=[], passages=0)
            yield TokenEvent(quick_answer.text)
            yield DoneEvent(quick_answer)
            return

        calls: list[LLMCall] = []
        standalone = self.standalone_question(question, history, trace, calls)

        retrieval = self.retriever.retrieve(standalone, trace)
        passages = retrieval.passages
        yield RetrievalEvent(documents=unique_titles(passages), passages=len(passages))

        if not passages:
            yield DoneEvent(
                self.abstained(standalone, AbstainReason.NO_RELEVANT_SOURCES, [], calls, trace)
            )
            return

        gate = AbstainGate(ABSTAIN_TOKEN)
        completion: Completion | None = None
        with trace.span("generate", model=self.config.answer_model) as span:
            for item in self.llm.stream(
                answer_messages(standalone, passages),
                model=self.config.answer_model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            ):
                if isinstance(item, Completion):
                    completion = item
                elif text := gate.feed(item):
                    yield TokenEvent(text)
            if text := gate.release():
                yield TokenEvent(text)
            if completion is None:
                raise LLMUnavailableError("The model stream ended early", reason="provider_error")
            span["completion_tokens"] = completion.usage.completion_tokens
        calls.append(LLMCall.from_completion("generate", completion))

        draft = normalize_citations(completion.text.strip())
        streamed = not gate.suppressed
        if is_abstention(draft):
            answer = self.abstained(
                standalone, AbstainReason.MODEL_DECLINED, passages, calls, trace
            )
        else:
            answer = self.enforce_citations(standalone, passages, draft, calls, trace)
        if streamed and answer.text != draft:
            yield ReplaceEvent(answer.text)
        yield DoneEvent(answer)

    def quick_answer(self, question: str, trace: Trace) -> Answer | None:
        normalized = " ".join(re.sub(r"[^a-z0-9\s]", " ", question.casefold()).split())

        if normalized in GREETING_QUESTIONS or normalized in {
            "hi how are you",
            "hey how are you",
            "hello how are you",
        }:
            text = "Hi! I'm here to help with questions about your policies and documents."
        elif normalized in WELLBEING_QUESTIONS:
            text = "I'm doing well! I can help with your documents."
        elif DOCUMENT_COUNT_QUESTION.search(normalized) and (
            normalized
            in {"how many documents", "how many docs", "how many files", "how many policies"}
            or DOCUMENT_COUNT_SCOPE.search(normalized)
        ):
            with trace.span("metadata.document_count"):
                count = len({chunk.document_id for chunk in self.retriever.store.all_chunks()})
            noun = "document" if count == 1 else "documents"
            text = f"I currently have {count} {noun} indexed and ready to search."
        else:
            return None

        return Answer(
            text=text,
            status=AnswerStatus.ANSWERED,
            standalone_question=question,
            trace=trace.to_dict(),
        )

    def standalone_question(
        self, question: str, history: Sequence[ChatMessage], trace: Trace, calls: list[LLMCall]
    ) -> str:
        recent = list(history)[-self.config.history_messages :]
        if not recent:
            return question
        with trace.span("rewrite", model=self.config.rewrite_model) as span:
            try:
                completion = self.llm.complete(
                    rewrite_messages(recent, question),
                    model=self.config.rewrite_model,
                    temperature=0.0,
                    max_tokens=400,
                )
            except LLMUnavailableError as exc:
                logger.warning(
                    "question rewrite failed", extra={"reason": exc.reason, "detail": exc.detail}
                )
                span["fallback"] = True
                return question
        calls.append(LLMCall.from_completion("rewrite", completion))
        rewritten = completion.text.strip().strip('"').removeprefix("Question:").strip()
        return rewritten[:1000] or question

    def enforce_citations(
        self,
        question: str,
        passages: list[Passage],
        draft: str,
        calls: list[LLMCall],
        trace: Trace,
    ) -> Answer:
        minimum = self.config.min_citation_coverage
        report = check_citations(draft, len(passages))
        if report.is_valid(minimum):
            return self.answered(question, draft, report, passages, calls, trace, repaired=False)

        with trace.span("repair", model=self.config.answer_model) as span:
            span["problems"] = report.problems(minimum)
            completion = self.llm.complete(
                repair_messages(question, passages, draft, report.problems(minimum)),
                model=self.config.answer_model,
                temperature=0.0,
                max_tokens=self.config.max_tokens,
            )
        calls.append(LLMCall.from_completion("repair", completion))
        revised = normalize_citations(completion.text.strip())
        if is_abstention(revised):
            return self.abstained(question, AbstainReason.MODEL_DECLINED, passages, calls, trace)
        revised_report = check_citations(revised, len(passages))
        if revised_report.is_valid(minimum):
            return self.answered(question, revised, revised_report, passages, calls, trace, True)
        logger.warning(
            "answer withheld after failed citation check",
            extra={"problems": revised_report.problems(minimum)},
        )
        return self.abstained(question, AbstainReason.CITATIONS_INVALID, passages, calls, trace)

    def answered(
        self,
        question: str,
        text: str,
        report: CitationReport,
        passages: list[Passage],
        calls: list[LLMCall],
        trace: Trace,
        repaired: bool,
    ) -> Answer:
        return Answer(
            text=text,
            status=AnswerStatus.ANSWERED,
            standalone_question=question,
            citations=[
                Citation.from_passage(number, passages[number - 1])
                for number in sorted(report.cited)
            ],
            passages=passages,
            citation_coverage=report.coverage,
            repaired=repaired,
            llm_calls=calls,
            trace=trace.to_dict(),
        )

    def abstained(
        self,
        question: str,
        reason: AbstainReason,
        passages: list[Passage],
        calls: list[LLMCall],
        trace: Trace,
    ) -> Answer:
        return Answer(
            text=NO_ANSWER_MESSAGE,
            status=AnswerStatus.ABSTAINED,
            standalone_question=question,
            passages=passages,
            abstain_reason=reason,
            llm_calls=calls,
            trace=trace.to_dict(),
        )
