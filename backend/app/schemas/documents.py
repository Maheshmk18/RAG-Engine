from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.db.records import DocumentStatus


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    filename: str
    content_type: str
    size_bytes: int
    status: DocumentStatus
    error_message: str | None
    chunk_count: int
    page_count: int | None
    created_at: datetime
    processed_at: datetime | None
