from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class DocumentStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"


class MessageStatus(StrEnum):
    ANSWERED = "answered"
    ABSTAINED = "abstained"
    FAILED = "failed"


@dataclass
class DocumentRecord:
    id: str
    title: str
    filename: str
    content_type: str
    size_bytes: int
    sha256: str
    file_id: Any
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime
    chunk_count: int = 0
    attempts: int = 0
    page_count: int | None = None
    error_message: str | None = None
    processed_at: datetime | None = None

    @classmethod
    def from_mongo(cls, raw: dict[str, Any]) -> "DocumentRecord":
        return cls(
            id=raw["_id"],
            title=raw["title"],
            filename=raw["filename"],
            content_type=raw["content_type"],
            size_bytes=raw["size_bytes"],
            sha256=raw["sha256"],
            file_id=raw["file_id"],
            status=DocumentStatus(raw["status"]),
            created_at=raw["created_at"],
            updated_at=raw["updated_at"],
            chunk_count=raw.get("chunk_count", 0),
            attempts=raw.get("attempts", 0),
            page_count=raw.get("page_count"),
            error_message=raw.get("error_message"),
            processed_at=raw.get("processed_at"),
        )


@dataclass
class SessionRecord:
    id: str
    client_id: str
    title: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_mongo(cls, raw: dict[str, Any]) -> "SessionRecord":
        return cls(
            id=raw["_id"],
            client_id=raw["client_id"],
            title=raw["title"],
            created_at=raw["created_at"],
            updated_at=raw["updated_at"],
        )


@dataclass
class MessageRecord:
    id: str
    session_id: str
    role: MessageRole
    content: str
    created_at: datetime
    status: MessageStatus | None = None
    citations: list[dict[str, Any]] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    feedback: int | None = None

    @classmethod
    def from_mongo(cls, raw: dict[str, Any]) -> "MessageRecord":
        return cls(
            id=raw["_id"],
            session_id=raw["session_id"],
            role=MessageRole(raw["role"]),
            content=raw["content"],
            created_at=raw["created_at"],
            status=MessageStatus(raw["status"]) if raw.get("status") else None,
            citations=raw.get("citations", []),
            metrics=raw.get("metrics", {}),
            feedback=raw.get("feedback"),
        )

    def to_mongo(self) -> dict[str, Any]:
        return {
            "_id": self.id,
            "session_id": self.session_id,
            "role": self.role.value,
            "content": self.content,
            "status": self.status.value if self.status else None,
            "citations": self.citations,
            "metrics": self.metrics,
            "feedback": self.feedback,
            "created_at": self.created_at,
        }
