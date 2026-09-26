from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pymongo.database import Database

from app.core.config import Settings
from app.ingestion.pipeline import IngestionPipeline
from app.retrieval.retriever import HybridRetriever, RetrievalConfig
from app.retrieval.store import PineconeChunkStore
from app.services import documents as document_service
from tests.fakes import HashingEmbedder, OverlapReranker

HANDBOOK = b"""# Handbook

## Hotels

Hotels are reimbursed up to 200 per night, or 275 in London.

## Remote Access

Connect through the company VPN before using internal systems.
"""


def index(
    db: Database, settings: Settings, store: PineconeChunkStore, name: str, data: bytes
) -> None:
    document = document_service.create_document(db, name, data, settings)
    IngestionPipeline(HashingEmbedder(), 100, 10, store).process(db, document.id)


@pytest.fixture
def store(app: FastAPI, db: Database, settings: Settings) -> PineconeChunkStore:
    index(db, settings, app.state.chunk_store, "handbook.md", HANDBOOK)
    store: PineconeChunkStore = app.state.chunk_store
    app.state.retriever = HybridRetriever(
        store, HashingEmbedder(), OverlapReranker(), RetrievalConfig(min_relevance=0.3)
    )
    return store


def search(client: TestClient, query: str) -> dict[str, Any]:
    response = client.post("/api/v1/retrieval/search", json={"query": query})
    assert response.status_code == 200
    body: dict[str, Any] = response.json()
    return body


def test_search_returns_scored_passages(client: TestClient, store: PineconeChunkStore) -> None:
    body = search(client, "VPN internal")
    top = body["passages"][0]
    assert top["heading"] == "Remote Access"
    assert top["document_title"] == "Handbook"
    assert top["lexical_rank"] == 1
    assert top["dense_rank"] is not None
    assert body["trace"]["spans"][0]["name"] == "retrieval.dense"


def test_indexes_follow_corpus_changes(
    client: TestClient, store: PineconeChunkStore, db: Database, settings: Settings
) -> None:
    assert search(client, "sabbatical eligibility")["passages"] == []
    extra = b"# Sabbatical\n\n## Eligibility\n\nSabbatical eligibility starts after seven years."
    index(db, settings, store, "sabbatical.md", extra)
    passages = search(client, "sabbatical eligibility")["passages"]
    assert passages[0]["document_title"] == "Sabbatical"


def test_pinecone_vector_search_ranks_by_similarity(store: PineconeChunkStore) -> None:
    ids = store.vector_search(HashingEmbedder().embed_query("hotels night London"), limit=2)
    records = store.get_many(ids)
    assert records[ids[0]].heading == "Hotels"
    assert len(store.all_chunks()) == 2
