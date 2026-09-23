import json
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pymongo.database import Database

from app.core.config import Settings
from app.core.rate_limit import SlidingWindowRateLimiter
from app.generation.answerer import AnswerConfig, AnswerService
from app.generation.llm import LLMUnavailableError
from app.ingestion.pipeline import IngestionPipeline
from app.retrieval.retriever import HybridRetriever, RetrievalConfig
from app.retrieval.store import MongoChunkStore
from app.services import documents as document_service
from tests.conftest import OTHER_CLIENT_ID
from tests.fakes import HashingEmbedder, OverlapReranker, ScriptedLLM

HANDBOOK = b"""# Leave Policy

## Entitlement

Full-time employees receive 25 days of paid annual leave per year.

## Carry-Over

Employees may carry over up to 5 unused leave days into the next year.
"""


@pytest.fixture
def llm(app: FastAPI, db: Database, settings: Settings) -> ScriptedLLM:
    embedder = HashingEmbedder()
    document = document_service.create_document(db, "leave.md", HANDBOOK, settings)
    IngestionPipeline(embedder, 100, 10).process(db, document.id)
    retriever = HybridRetriever(
        MongoChunkStore(app.state.database),
        embedder,
        OverlapReranker(),
        RetrievalConfig(top_k=2, min_relevance=0.3),
    )
    scripted = ScriptedLLM()
    app.state.answer_service = AnswerService(
        retriever, scripted, AnswerConfig("answer-model", "rewrite-model")
    )
    return scripted


def read_events(response: Any) -> list[tuple[str, dict[str, Any]]]:
    events = []
    for block in response.text.strip().split("\n\n"):
        lines = dict(line.split(": ", 1) for line in block.splitlines())
        events.append((lines["event"], json.loads(lines["data"])))
    return events


def new_session(client: TestClient, headers: dict[str, str]) -> str:
    return client.post("/api/v1/chat/sessions", json={}, headers=headers).json()["id"]


def ask(client: TestClient, headers: dict[str, str], session_id: str, question: str) -> list:
    response = client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={"content": question},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    return read_events(response)


def test_question_streams_answer_with_citations(
    client: TestClient, visitor: dict[str, str], llm: ScriptedLLM
) -> None:
    session_id = new_session(client, visitor)
    llm.answers.append("Full-time employees receive 25 days of paid annual leave [1].")

    events = ask(client, visitor, session_id, "How many days of annual leave do I get?")
    names = [name for name, _ in events]
    assert names[:2] == ["question", "retrieval"]
    assert "token" in names
    assert names[-1] == "answer"
    answer = events[-1][1]
    assert answer["status"] == "answered"
    assert answer["citations"][0]["heading"] == "Entitlement"

    detail = client.get(f"/api/v1/chat/sessions/{session_id}", headers=visitor).json()
    assert detail["title"] == "How many days of annual leave do I get?"
    assert [message["role"] for message in detail["messages"]] == ["user", "assistant"]
    assert detail["messages"][1]["citations"][0]["document_title"] == "Leave Policy"


def test_follow_up_uses_conversation_history(
    client: TestClient, visitor: dict[str, str], llm: ScriptedLLM
) -> None:
    session_id = new_session(client, visitor)
    llm.answers.append("Full-time employees receive 25 days of paid annual leave [1].")
    ask(client, visitor, session_id, "How many days of annual leave do I get?")

    llm.completions.append("How many unused leave days can employees carry over?")
    llm.answers.append("Employees may carry over up to 5 unused leave days [1].")
    events = ask(client, visitor, session_id, "Can I keep some for next year?")

    assert "How many days of annual leave do I get?" in llm.calls[1][1][-1]["content"]
    assert events[-1][1]["citations"][0]["heading"] == "Carry-Over"


def test_unanswerable_question_abstains(
    client: TestClient, visitor: dict[str, str], llm: ScriptedLLM
) -> None:
    events = ask(client, visitor, new_session(client, visitor), "Where is the bike storage?")
    assert events[-1][1]["status"] == "abstained"
    assert llm.calls == []


def test_model_outage_is_reported_and_recorded(
    client: TestClient, visitor: dict[str, str], llm: ScriptedLLM
) -> None:
    session_id = new_session(client, visitor)
    llm.failure = LLMUnavailableError("limited", reason="rate_limited")
    events = ask(client, visitor, session_id, "How many days of annual leave do I get?")
    assert events[-1][0] == "error"
    detail = client.get(f"/api/v1/chat/sessions/{session_id}", headers=visitor).json()
    assert detail["messages"][-1]["status"] == "failed"


def test_feedback_is_saved_on_answers(
    client: TestClient, visitor: dict[str, str], llm: ScriptedLLM
) -> None:
    llm.answers.append("Full-time employees receive 25 days of paid annual leave [1].")
    events = ask(client, visitor, new_session(client, visitor), "How much annual leave?")
    answer_id, question_id = events[-1][1]["id"], events[0][1]["id"]

    rated = client.post(
        f"/api/v1/chat/messages/{answer_id}/feedback", json={"value": -1}, headers=visitor
    )
    assert rated.json()["feedback"] == -1
    rejected = client.post(
        f"/api/v1/chat/messages/{question_id}/feedback", json={"value": 1}, headers=visitor
    )
    assert rejected.status_code == 404


def test_conversations_belong_to_one_browser(
    client: TestClient, visitor: dict[str, str], llm: ScriptedLLM
) -> None:
    session_id = new_session(client, visitor)
    other = {"X-Client-Id": OTHER_CLIENT_ID}
    assert client.get(f"/api/v1/chat/sessions/{session_id}", headers=other).status_code == 404
    assert client.get("/api/v1/chat/sessions", headers=other).json() == []
    response = client.post(
        f"/api/v1/chat/sessions/{session_id}/messages", json={"content": "hi"}, headers=other
    )
    assert response.status_code == 404


def test_rename_and_delete_session(client: TestClient, visitor: dict[str, str]) -> None:
    session_id = new_session(client, visitor)
    renamed = client.patch(
        f"/api/v1/chat/sessions/{session_id}", json={"title": "Leave questions"}, headers=visitor
    )
    assert renamed.json()["title"] == "Leave questions"
    assert client.delete(f"/api/v1/chat/sessions/{session_id}", headers=visitor).status_code == 204
    assert client.get("/api/v1/chat/sessions", headers=visitor).json() == []


def test_questions_are_rate_limited(
    app: FastAPI, client: TestClient, visitor: dict[str, str], llm: ScriptedLLM
) -> None:
    app.state.chat_limiter = SlidingWindowRateLimiter(limit=1, window_seconds=60)
    session_id = new_session(client, visitor)
    ask(client, visitor, session_id, "Where is the bike storage?")
    response = client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={"content": "Where is the bike storage?"},
        headers=visitor,
    )
    assert response.status_code == 429
