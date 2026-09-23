import uuid
from datetime import datetime

from pydantic import BaseModel

from app.db.models import Document, DocumentStatus


class DocumentRead(BaseModel):
    id: uuid.UUID
    title: str
    filename: str
    content_type: str
    size_bytes: int
    status: DocumentStatus
    error_message: str | None
    chunk_count: int
    page_count: int | None
    uploaded_by: str | None
    created_at: datetime
    processed_at: datetime | None

    @classmethod
    def from_model(cls, document: Document) -> "DocumentRead":
        return cls(
            id=document.id,
            title=document.title,
            filename=document.filename,
            content_type=document.content_type,
            size_bytes=document.size_bytes,
            status=document.status,
            error_message=document.error_message,
            chunk_count=document.chunk_count,
            page_count=document.page_count,
            uploaded_by=document.uploaded_by.full_name if document.uploaded_by else None,
            created_at=document.created_at,
            processed_at=document.processed_at,
        )
