import hashlib
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import (
    ConflictError,
    NotFoundError,
    PayloadTooLargeError,
    UnsupportedMediaError,
)
from app.db.models import Document, DocumentFile, DocumentStatus, User
from app.ingestion.extract import (
    CONTENT_TYPES,
    FileKind,
    detect_kind,
    looks_like_valid_file,
    title_from_filename,
)
from app.services.corpus import bump_corpus_version

SUPPORTED_FORMATS = ", ".join(kind.value.upper() for kind in FileKind)


def create_document(
    db: Session, filename: str, data: bytes, uploaded_by: User | None, settings: Settings
) -> Document:
    kind = detect_kind(filename)
    if kind is None:
        raise UnsupportedMediaError(f"Unsupported file type. Upload {SUPPORTED_FORMATS} files.")
    if len(data) > settings.max_upload_bytes:
        raise PayloadTooLargeError(f"Files must be smaller than {settings.max_upload_mb} MB")
    if not data or not looks_like_valid_file(kind, data):
        raise UnsupportedMediaError(f"The file is empty or is not a valid {kind.value.upper()}")

    digest = hashlib.sha256(data).hexdigest()
    existing = db.scalar(select(Document).where(Document.sha256 == digest))
    if existing is not None:
        raise ConflictError(
            f"This file is already in the knowledge base as '{existing.title}'",
            code="duplicate_document",
        )

    document = Document(
        title=title_from_filename(filename),
        filename=filename,
        content_type=CONTENT_TYPES[kind],
        size_bytes=len(data),
        sha256=digest,
        status=DocumentStatus.PENDING,
        chunk_count=0,
        attempts=0,
        uploaded_by=uploaded_by,
    )
    document.file = DocumentFile(data=data)
    db.add(document)
    db.commit()
    return document


def list_documents(db: Session) -> list[Document]:
    return list(db.scalars(select(Document).order_by(Document.created_at.desc())))


def get_document(db: Session, document_id: uuid.UUID) -> Document:
    document = db.get(Document, document_id)
    if document is None:
        raise NotFoundError("Document not found")
    return document


def get_document_file(db: Session, document_id: uuid.UUID) -> tuple[Document, bytes]:
    document = get_document(db, document_id)
    return document, document.file.data


def delete_document(db: Session, document_id: uuid.UUID) -> None:
    document = get_document(db, document_id)
    db.delete(document)
    bump_corpus_version(db)
    db.commit()


def reprocess_document(db: Session, document_id: uuid.UUID) -> Document:
    document = get_document(db, document_id)
    if document.status is DocumentStatus.PROCESSING:
        raise ConflictError("The document is already being processed")
    document.status = DocumentStatus.PENDING
    document.attempts = 0
    document.error_message = None
    db.commit()
    return document
