from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pymongo.database import Database

from app.core.config import Settings
from app.core.rate_limit import SlidingWindowRateLimiter
from app.db.mongo import CHUNKS, DOCUMENTS
from app.ingestion.pipeline import IngestionPipeline
from app.ingestion.worker import IngestionWorker
from app.services.corpus import current_corpus_version
from tests.fakes import HashingEmbedder

POLICY = b"""# Travel Policy

## Hotels

Hotels are reimbursed up to 200 per night, or 275 in London.

## Meals

Meals are reimbursed up to 60 per day for domestic travel.
"""


@pytest.fixture
def worker(app: FastAPI) -> IngestionWorker:
    pipeline = IngestionPipeline(
        HashingEmbedder(), max_words=120, overlap_words=20, vector_store=app.state.chunk_store
    )
    return IngestionWorker(
        app.state.database, pipeline, max_attempts=2, stale_after_seconds=600, poll_seconds=0
    )


def upload(client: TestClient, name: str, data: bytes) -> dict[str, Any]:
    response = client.post("/api/v1/documents", files={"file": (name, data)})
    return {**response.json(), "http_status": response.status_code}


def test_upload_is_queued_then_indexed_by_worker(
    client: TestClient, worker: IngestionWorker, db: Database
) -> None:
    created = upload(client, "travel.md", POLICY)
    assert created["http_status"] == 202
    assert created["status"] == "pending"

    assert worker.run_once() is True
    assert worker.run_once() is False

    document = client.get(f"/api/v1/documents/{created['id']}").json()
    assert document["status"] == "ready"
    assert document["title"] == "Travel Policy"
    assert document["chunk_count"] == 2
    headings = [chunk["heading"] for chunk in db[CHUNKS].find().sort("ordinal", 1)]
    assert headings == ["Hotels", "Meals"]
    assert current_corpus_version(db) == 1


def test_document_management_is_open(client: TestClient) -> None:
    created = upload(client, "travel.md", POLICY)
    assert created["http_status"] == 202
    path = f"/api/v1/documents/{created['id']}"
    assert client.post(f"{path}/reprocess").status_code == 200
    assert client.delete(path).status_code == 204


def test_uploads_are_rate_limited(app: FastAPI, client: TestClient) -> None:
    app.state.upload_limiter = SlidingWindowRateLimiter(limit=1, window_seconds=3600)
    assert upload(client, "travel.md", POLICY)["http_status"] == 202
    limited = upload(client, "other.md", b"# Other\n\nSome text.")
    assert limited["http_status"] == 429


def test_anyone_can_read_documents(client: TestClient) -> None:
    upload(client, "travel.md", POLICY)
    listed = client.get("/api/v1/documents").json()
    assert [item["filename"] for item in listed] == ["travel.md"]
    download = client.get(f"/api/v1/documents/{listed[0]['id']}/file")
    assert download.content == POLICY
    assert "travel.md" in download.headers["content-disposition"]


def test_duplicate_upload_is_rejected(client: TestClient) -> None:
    upload(client, "travel.md", POLICY)
    duplicate = upload(client, "copy-of-travel.md", POLICY)
    assert duplicate["http_status"] == 409
    assert duplicate["error"]["code"] == "duplicate_document"


@pytest.mark.parametrize(
    ("name", "data"),
    [
        ("archive.zip", b"PK\x03\x04"),
        ("fake.pdf", b"plain text pretending to be a pdf"),
        ("empty.txt", b""),
    ],
)
def test_invalid_uploads_are_rejected(
    client: TestClient, name: str, data: bytes
) -> None:
    assert upload(client, name, data)["http_status"] == 415


def test_oversized_upload_is_rejected(
    client: TestClient, settings: Settings
) -> None:
    data = b"a " * (settings.max_upload_bytes // 2 + 1)
    assert upload(client, "huge.txt", data)["http_status"] == 413


def test_unreadable_document_fails_permanently(
    client: TestClient, worker: IngestionWorker
) -> None:
    created = upload(client, "broken.pdf", b"%PDF-1.4 truncated")
    worker.run_once()
    document = client.get(f"/api/v1/documents/{created['id']}").json()
    assert document["status"] == "failed"
    assert document["error_message"] == "The PDF could not be read"


def test_transient_failures_are_retried(
    client: TestClient,
    worker: IngestionWorker,
    db: Database,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created = upload(client, "travel.md", POLICY)
    calls = {"count": 0}
    original = worker.pipeline.embedder.embed_documents

    def flaky(texts: list[str]) -> list[list[float]]:
        calls["count"] += 1
        if calls["count"] == 1:
            raise ConnectionError("model server unavailable")
        return original(texts)

    monkeypatch.setattr(worker.pipeline.embedder, "embed_documents", flaky)
    worker.run_once()
    assert db[DOCUMENTS].find_one({"_id": created["id"]})["status"] == "pending"
    worker.run_once()
    assert db[DOCUMENTS].find_one({"_id": created["id"]})["status"] == "ready"


def test_stale_processing_documents_are_reclaimed(
    client: TestClient, worker: IngestionWorker, db: Database
) -> None:
    created = upload(client, "travel.md", POLICY)
    assert worker.claim_next() == created["id"]
    assert worker.claim_next() is None
    worker.stale_after = worker.stale_after * 0
    assert worker.claim_next() == created["id"]
    assert db[DOCUMENTS].find_one({"_id": created["id"]})["attempts"] == 2


def test_delete_removes_chunks_and_file(
    client: TestClient, worker: IngestionWorker, db: Database
) -> None:
    created = upload(client, "travel.md", POLICY)
    worker.run_once()
    response = client.delete(f"/api/v1/documents/{created['id']}")
    assert response.status_code == 204
    assert db[CHUNKS].count_documents({}) == 0
    assert db["document_files.files"].count_documents({}) == 0
    assert current_corpus_version(db) == 2


def test_reprocess_requeues_document(
    client: TestClient, worker: IngestionWorker
) -> None:
    created = upload(client, "travel.md", POLICY)
    worker.run_once()
    response = client.post(f"/api/v1/documents/{created['id']}/reprocess")
    assert response.json()["status"] == "pending"
    assert worker.run_once() is True
