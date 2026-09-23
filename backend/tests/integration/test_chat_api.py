import json
from collections.abc import Callable
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.rate_limit import SlidingWindowRateLimiter
from app.db.models import User, UserRole
from app.generation.answerer import AnswerConfig, AnswerService
from app.generation.llm import LLMUnavailableError
from app.ingestion.pipeline import IngestionPipeline
from app.retrieval.retriever import HybridRetriever, RetrievalConfig
from app.retrieval.store import PostgresChunkStore
from app.services import documents as document_service
from tests.fakes import HashingEmbedder, OverlapReranker, ScriptedLLM

Headers = Callable[[User], dict[str, str]]

HANDBOOK = b"""# Leave Policy

## Entitlement

Full-time employees receive 25 days of paid annual leave per year.

## Carry-Over

Employees may carry over up to 5 unused leave days into the next year.
"""


@pytest.fixture
def llm(app: FastAPI, db: Session, admin: User, settings: Settings) -> ScriptedLLM:
    embedder = HashingEmbedder()
    document = document_service.create_document(db, "leave.md", HANDBOOK, admin, settings)
    IngestionPipeline(embedder, 100, 10).process(db, document.id)
    retriever = HybridRetriever(
        PostgresChunkStore(app.state.session_factory),
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


def ask(client: TestClient, headers: dict[str, str], session_id: str, question: str) -> list:
    response = client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={"content": question},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    return read_events(response)


def new_session(client: TestClient, headers: dict[str, str]) -> str:
    return client.post("/api/v1/chat/sessions", json={}, headers=headers).json()["id"]


def test_question_streams_answer_with_citations(
    client: TestClient, member: User, auth_headers: Headers, llm: ScriptedLLM
) -> None:
    headers = auth_headers(member)
    session_id = new_session(client, headers)
    llm.answers.append("Full-time employees receive 25 days of paid annual leave [1].")

    events = ask(client, headers, session_id, "How many days of annual leave do I get?")
    names = [name for name, _ in events]
    assert names[0] == "question"
    assert names[1] == "retrieval"
    assert "token" in names
    assert names[-1] == "answer"

    answer = events[-1][1]
    assert answer["status"] == "answered"
    assert answer["citations"][0]["heading"] == "Entitlement"
    assert answer["citations"][0]["number"] == 1

    detail = client.get(f"/api/v1/chat/sessions/{session_id}", headers=headers).json()
    assert detail["title"] == "How many days of annual leave do I get?"
    assert [message["role"] for message in detail["messages"]] == ["user", "assistant"]
    assert detail["messages"][1]["citations"][0]["document_title"] == "Leave Policy"


def test_follow_up_uses_conversation_history(
    client: TestClient, member: User, auth_headers: Headers, llm: ScriptedLLM
) -> None:
    headers = auth_headers(member)
    session_id = new_session(client, headers)
    llm.answers.append("Full-time employees receive 25 days of paid annual leave [1].")
    ask(client, headers, session_id, "How many days of annual leave do I get?")

    llm.completions.append("How many unused leave days can employees carry over?")
    llm.answers.append("Employees may carry over up to 5 unused leave days [1].")
    events = ask(client, headers, session_id, "Can I keep some for next year?")

    rewrite_prompt = llm.calls[1][1][-1]["content"]
    assert "How many days of annual leave do I get?" in rewrite_prompt
    assert events[-1][1]["citations"][0]["heading"] == "Carry-Over"


def test_unanswerable_question_abstains(
    client: TestClient, member: User, auth_headers: Headers, llm: ScriptedLLM
) -> None:
    headers = auth_headers(member)
    events = ask(client, headers, new_session(client, headers), "Where is the bike storage?")
    assert events[-1][1]["status"] == "abstained"
    assert events[-1][1]["citations"] == []
    assert llm.calls == []


def test_model_outage_is_reported_and_recorded(
    client: TestClient, member: User, auth_headers: Headers, llm: ScriptedLLM
) -> None:
    headers = auth_headers(member)
    session_id = new_session(client, headers)
    llm.failure = LLMUnavailableError("limited", reason="rate_limited")

    events = ask(client, headers, session_id, "How many days of annual leave do I get?")
    assert events[-1][0] == "error"
    assert events[-1][1]["status"] == "failed"
    detail = client.get(f"/api/v1/chat/sessions/{session_id}", headers=headers).json()
    assert detail["messages"][-1]["status"] == "failed"


def test_feedback_is_saved_on_answers(
    client: TestClient, member: User, auth_headers: Headers, llm: ScriptedLLM
) -> None:
    headers = auth_headers(member)
    llm.answers.append("Full-time employees receive 25 days of paid annual leave [1].")
    events = ask(client, headers, new_session(client, headers), "How much annual leave?")
    answer_id = events[-1][1]["id"]
    question_id = events[0][1]["id"]

    response = client.post(
        f"/api/v1/chat/messages/{answer_id}/feedback", json={"value": -1}, headers=headers
    )
    assert response.json()["feedback"] == -1
    rejected = client.post(
        f"/api/v1/chat/messages/{question_id}/feedback", json={"value": 1}, headers=headers
    )
    assert rejected.status_code == 404


def test_sessions_are_private(
    client: TestClient,
    member: User,
    make_user: Callable[..., User],
    auth_headers: Headers,
    llm: ScriptedLLM,
) -> None:
    session_id = new_session(client, auth_headers(member))
    other = make_user("other@example.com", UserRole.MEMBER)
    other_headers = auth_headers(other)
    assert (
        client.get(f"/api/v1/chat/sessions/{session_id}", headers=other_headers).status_code == 404
    )
    assert client.get("/api/v1/chat/sessions", headers=other_headers).json() == []
    response = client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={"content": "hello"},
        headers=other_headers,
    )
    assert response.status_code == 404


def test_rename_and_delete_session(client: TestClient, member: User, auth_headers: Headers) -> None:
    headers = auth_headers(member)
    session_id = new_session(client, headers)
    renamed = client.patch(
        f"/api/v1/chat/sessions/{session_id}", json={"title": "Leave questions"}, headers=headers
    )
    assert renamed.json()["title"] == "Leave questions"
    assert client.delete(f"/api/v1/chat/sessions/{session_id}", headers=headers).status_code == 204
    assert client.get("/api/v1/chat/sessions", headers=headers).json() == []


def test_questions_are_rate_limited(
    app: FastAPI, client: TestClient, member: User, auth_headers: Headers, llm: ScriptedLLM
) -> None:
    app.state.chat_limiter = SlidingWindowRateLimiter(limit=1, window_seconds=60)
    headers = auth_headers(member)
    session_id = new_session(client, headers)
    ask(client, headers, session_id, "Where is the bike storage?")
    response = client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={"content": "Where is the bike storage?"},
        headers=headers,
    )
    assert response.status_code == 429
