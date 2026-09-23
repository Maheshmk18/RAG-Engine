import hashlib
import uuid

import gridfs
from pymongo import DESCENDING, ReturnDocument
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from app.core.config import Settings
from app.core.errors import (
    ConflictError,
    NotFoundError,
    PayloadTooLargeError,
    UnsupportedMediaError,
)
from app.db.mongo import CHUNKS, DOCUMENTS, FILES, utcnow
from app.db.records import DocumentRecord, DocumentStatus
from app.ingestion.extract import (
    CONTENT_TYPES,
    FileKind,
    detect_kind,
    looks_like_valid_file,
    title_from_filename,
)
from app.services.corpus import bump_corpus_version

SUPPORTED_FORMATS = ", ".join(kind.value.upper() for kind in FileKind)


def file_store(db: Database) -> gridfs.GridFS:
    return gridfs.GridFS(db, collection=FILES)


def create_document(db: Database, filename: str, data: bytes, settings: Settings) -> DocumentRecord:
    kind = detect_kind(filename)
    if kind is None:
        raise UnsupportedMediaError(f"Unsupported file type. Upload {SUPPORTED_FORMATS} files.")
    if len(data) > settings.max_upload_bytes:
        raise PayloadTooLargeError(f"Files must be smaller than {settings.max_upload_mb} MB")
    if not data or not looks_like_valid_file(kind, data):
        raise UnsupportedMediaError(f"The file is empty or is not a valid {kind.value.upper()}")

    digest = hashlib.sha256(data).hexdigest()
    existing = db[DOCUMENTS].find_one({"sha256": digest}, {"title": 1})
    if existing is not None:
        raise ConflictError(
            f"This file is already in the knowledge base as '{existing['title']}'",
            code="duplicate_document",
        )

    files = file_store(db)
    file_id = files.put(data, filename=filename, content_type=CONTENT_TYPES[kind])
    now = utcnow()
    raw = {
        "_id": str(uuid.uuid4()),
        "title": title_from_filename(filename),
        "filename": filename,
        "content_type": CONTENT_TYPES[kind],
        "size_bytes": len(data),
        "sha256": digest,
        "file_id": file_id,
        "status": DocumentStatus.PENDING.value,
        "chunk_count": 0,
        "attempts": 0,
        "page_count": None,
        "error_message": None,
        "processed_at": None,
        "created_at": now,
        "updated_at": now,
    }
    try:
        db[DOCUMENTS].insert_one(raw)
    except DuplicateKeyError as exc:
        files.delete(file_id)
        raise ConflictError(
            "This file is already in the knowledge base", code="duplicate_document"
        ) from exc
    return DocumentRecord.from_mongo(raw)


def list_documents(db: Database) -> list[DocumentRecord]:
    cursor = db[DOCUMENTS].find().sort("created_at", DESCENDING)
    return [DocumentRecord.from_mongo(raw) for raw in cursor]


def get_document(db: Database, document_id: str) -> DocumentRecord:
    raw = db[DOCUMENTS].find_one({"_id": document_id})
    if raw is None:
        raise NotFoundError("Document not found")
    return DocumentRecord.from_mongo(raw)


def read_file(db: Database, document: DocumentRecord) -> bytes:
    data: bytes = file_store(db).get(document.file_id).read()
    return data


def delete_document(db: Database, document_id: str) -> None:
    document = get_document(db, document_id)
    db[CHUNKS].delete_many({"document_id": document_id})
    db[DOCUMENTS].delete_one({"_id": document_id})
    file_store(db).delete(document.file_id)
    bump_corpus_version(db)


def reprocess_document(db: Database, document_id: str) -> DocumentRecord:
    raw = db[DOCUMENTS].find_one_and_update(
        {"_id": document_id, "status": {"$ne": DocumentStatus.PROCESSING.value}},
        {
            "$set": {
                "status": DocumentStatus.PENDING.value,
                "attempts": 0,
                "error_message": None,
                "updated_at": utcnow(),
            }
        },
        return_document=ReturnDocument.AFTER,
    )
    if raw is None:
        get_document(db, document_id)
        raise ConflictError("The document is already being processed")
    return DocumentRecord.from_mongo(raw)
