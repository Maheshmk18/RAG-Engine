from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.db.records import MessageRole, MessageStatus

Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]


class CitationRead(BaseModel):
    number: int
    chunk_id: str
    document_id: str
    document_title: str
    heading: str | None
    page: int | None
    text: str
    relevance: float


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    role: MessageRole
    content: str
    status: MessageStatus | None
    citations: list[CitationRead]
    feedback: int | None
    created_at: datetime


class SessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    created_at: datetime
    updated_at: datetime


class SessionDetail(SessionRead):
    messages: list[MessageRead]


class SessionCreate(BaseModel):
    title: Title | None = None


class SessionUpdate(BaseModel):
    title: Title


class QuestionRequest(BaseModel):
    content: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class FeedbackRequest(BaseModel):
    value: Literal[1, -1] | None = Field(default=None)
