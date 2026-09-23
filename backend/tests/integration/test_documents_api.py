import uuid
from collections.abc import Callable

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.models import Chunk, Document, DocumentStatus, User
from app.ingestion.pipeline import IngestionPipeline
from app.ingestion.worker import IngestionWorker
from app.services.corpus import current_corpus_version
from tests.fakes import HashingEmbedder

Headers = Callable[[User], dict[str, str]]

POLICY = b"""# Travel Policy

## Hotels

Hotels are reimbursed up to 200 per night, or 275 in London.

## Meals

Meals are reimbursed up to 60 per day for domestic travel.
"""


@pytest.fixture
def worker(app: FastAPI, settings: Settings) -> IngestionWorker:
    pipeline = IngestionPipeline(HashingEmbedder(), max_words=120, overlap_words=20)
    return IngestionWorker(
        app.state.session_factory, pipeline, max_attempts=2, stale_after_seconds=600, poll_seconds=0
    )


def upload(client: TestClient, headers: dict[str, str], name: str, data: bytes) -> dict:
    response = client.post("/api/v1/documents", files={"file": (name, data)}, headers=headers)
    return {**response.json(), "http_status": response.status_code}


def test_upload_is_queued_then_indexed_by_worker(
    client: TestClient, admin: User, auth_headers: Headers, worker: IngestionWorker, db: Session
) -> None:
    created = upload(client, auth_headers(admin), "travel.md", POLICY)
    assert created["http_status"] == 202
    assert created["uploaded_by"] == "Test User"
    assert created["error_message"] is None

    assert worker.run_once() is True
    assert worker.run_once() is False

    document = client.get(f"/api/v1/documents/{created['id']}", headers=auth_headers(admin)).json()
    assert document["status"] == "ready"
    assert document["title"] == "Travel Policy"
    assert document["chunk_count"] == 2
    headings = db.scalars(select(Chunk.heading).order_by(Chunk.ordinal)).all()
    assert headings == ["Hotels", "Meals"]
    assert current_corpus_version(db) == 1


def test_duplicate_upload_is_rejected(
    client: TestClient, admin: User, auth_headers: Headers
) -> None:
    upload(client, auth_headers(admin), "travel.md", POLICY)
    duplicate = upload(client, auth_headers(admin), "copy-of-travel.md", POLICY)
    assert duplicate["http_status"] == 409
    assert duplicate["error"]["code"] == "duplicate_document"


@pytest.mark.parametrize(
    ("name", "data", "status"),
    [
        ("archive.zip", b"PK\x03\x04", 415),
        ("fake.pdf", b"plain text pretending to be a pdf", 415),
        ("empty.txt", b"", 415),
    ],
)
def test_invalid_uploads_are_rejected(
    client: TestClient, admin: User, auth_headers: Headers, name: str, data: bytes, status: int
) -> None:
    assert upload(client, auth_headers(admin), name, data)["http_status"] == status


def test_oversized_upload_is_rejected(
    client: TestClient, admin: User, auth_headers: Headers, settings: Settings
) -> None:
    data = b"a " * (settings.max_upload_bytes // 2 + 1)
    assert upload(client, auth_headers(admin), "huge.txt", data)["http_status"] == 413


def test_members_can_read_but_not_upload(
    client: TestClient, admin: User, member: User, auth_headers: Headers
) -> None:
    upload(client, auth_headers(admin), "travel.md", POLICY)
    assert (
        upload(client, auth_headers(member), "other.md", b"# Other\n\nText")["http_status"] == 403
    )
    listed = client.get("/api/v1/documents", headers=auth_headers(member)).json()
    assert [item["filename"] for item in listed] == ["travel.md"]

    download = client.get(f"/api/v1/documents/{listed[0]['id']}/file", headers=auth_headers(member))
    assert download.content == POLICY
    assert "travel.md" in download.headers["content-disposition"]


def test_unreadable_document_fails_permanently(
    client: TestClient, admin: User, auth_headers: Headers, worker: IngestionWorker
) -> None:
    created = upload(client, auth_headers(admin), "broken.pdf", b"%PDF-1.4 truncated")
    worker.run_once()
    document = client.get(f"/api/v1/documents/{created['id']}", headers=auth_headers(admin)).json()
    assert document["status"] == "failed"
    assert document["error_message"] == "The PDF could not be read"


def test_transient_failures_are_retried(
    client: TestClient,
    admin: User,
    auth_headers: Headers,
    worker: IngestionWorker,
    db: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created = upload(client, auth_headers(admin), "travel.md", POLICY)
    calls = {"count": 0}
    original = worker.pipeline.embedder.embed_documents

    def flaky(texts: list[str]) -> list[list[float]]:
        calls["count"] += 1
        if calls["count"] == 1:
            raise ConnectionError("model server unavailable")
        return original(texts)

    monkeypatch.setattr(worker.pipeline.embedder, "embed_documents", flaky)
    document_id = uuid.UUID(created["id"])
    worker.run_once()
    assert db.get(Document, document_id).status is DocumentStatus.PENDING
    db.expire_all()
    worker.run_once()
    assert db.get(Document, document_id).status is DocumentStatus.READY


def test_delete_removes_chunks_and_bumps_version(
    client: TestClient, admin: User, auth_headers: Headers, worker: IngestionWorker, db: Session
) -> None:
    created = upload(client, auth_headers(admin), "travel.md", POLICY)
    worker.run_once()
    response = client.delete(f"/api/v1/documents/{created['id']}", headers=auth_headers(admin))
    assert response.status_code == 204
    assert db.scalar(select(func.count()).select_from(Chunk)) == 0
    assert current_corpus_version(db) == 2


def test_reprocess_requeues_document(
    client: TestClient, admin: User, auth_headers: Headers, worker: IngestionWorker
) -> None:
    created = upload(client, auth_headers(admin), "travel.md", POLICY)
    worker.run_once()
    response = client.post(
        f"/api/v1/documents/{created['id']}/reprocess", headers=auth_headers(admin)
    )
    assert response.json()["status"] == "pending"
    assert worker.run_once() is True
