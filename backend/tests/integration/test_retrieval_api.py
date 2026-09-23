from collections.abc import Callable

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.models import User
from app.ingestion.pipeline import IngestionPipeline
from app.retrieval.retriever import HybridRetriever, RetrievalConfig
from app.retrieval.store import PostgresChunkStore
from app.services import documents as document_service
from tests.fakes import HashingEmbedder, OverlapReranker

Headers = Callable[[User], dict[str, str]]

HANDBOOK = b"""# Handbook

## Hotels

Hotels are reimbursed up to 200 per night, or 275 in London.

## Remote Access

Connect through the company VPN before using internal systems.
"""


@pytest.fixture
def indexed(app: FastAPI, db: Session, admin: User, settings: Settings) -> PostgresChunkStore:
    embedder = HashingEmbedder()
    document = document_service.create_document(db, "handbook.md", HANDBOOK, admin, settings)
    IngestionPipeline(embedder, max_words=100, overlap_words=10).process(db, document.id)
    store = PostgresChunkStore(app.state.session_factory)
    app.state.retriever = HybridRetriever(
        store, embedder, OverlapReranker(), RetrievalConfig(min_relevance=0.3)
    )
    return store


def test_search_returns_scored_passages(
    client: TestClient, admin: User, auth_headers: Headers, indexed: PostgresChunkStore
) -> None:
    response = client.post(
        "/api/v1/retrieval/search", json={"query": "VPN internal"}, headers=auth_headers(admin)
    )
    assert response.status_code == 200
    body = response.json()
    top = body["passages"][0]
    assert top["heading"] == "Remote Access"
    assert top["document_title"] == "Handbook"
    assert top["lexical_rank"] == 1
    assert body["trace"]["spans"][0]["name"] == "retrieval.dense"


def test_lexical_index_follows_corpus_changes(
    client: TestClient,
    admin: User,
    auth_headers: Headers,
    indexed: PostgresChunkStore,
    db: Session,
    settings: Settings,
) -> None:
    headers = auth_headers(admin)
    query = {"query": "sabbatical eligibility"}
    assert (
        client.post("/api/v1/retrieval/search", json=query, headers=headers).json()["passages"]
        == []
    )

    extra = b"# Sabbatical\n\n## Eligibility\n\nSabbatical eligibility starts after seven years."
    document = document_service.create_document(db, "sabbatical.md", extra, admin, settings)
    IngestionPipeline(HashingEmbedder(), 100, 10).process(db, document.id)

    passages = client.post("/api/v1/retrieval/search", json=query, headers=headers).json()[
        "passages"
    ]
    assert passages[0]["document_title"] == "Sabbatical"


def test_search_is_admin_only(client: TestClient, member: User, auth_headers: Headers) -> None:
    response = client.post(
        "/api/v1/retrieval/search", json={"query": "vpn"}, headers=auth_headers(member)
    )
    assert response.status_code == 403
