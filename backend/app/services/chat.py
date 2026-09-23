import uuid
from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.db.models import ChatSession, Message, MessageRole, MessageStatus, User
from app.generation.answerer import Answer
from app.generation.llm import ChatMessage

DEFAULT_TITLE = "New conversation"
TITLE_LENGTH = 60


def title_from_question(question: str) -> str:
    text = " ".join(question.split())
    if len(text) <= TITLE_LENGTH:
        return text
    return text[:TITLE_LENGTH].rsplit(" ", 1)[0] + "..."


def list_sessions(db: Session, user: User, limit: int = 100) -> list[ChatSession]:
    query = (
        select(ChatSession)
        .where(ChatSession.user_id == user.id)
        .order_by(ChatSession.updated_at.desc())
        .limit(limit)
    )
    return list(db.scalars(query))


def create_session(db: Session, user: User, title: str | None = None) -> ChatSession:
    session = ChatSession(user_id=user.id, title=title or DEFAULT_TITLE)
    db.add(session)
    db.commit()
    return session


def get_session(db: Session, user: User, session_id: uuid.UUID) -> ChatSession:
    session = db.get(ChatSession, session_id)
    if session is None or session.user_id != user.id:
        raise NotFoundError("Conversation not found")
    return session


def rename_session(db: Session, user: User, session_id: uuid.UUID, title: str) -> ChatSession:
    session = get_session(db, user, session_id)
    session.title = title
    db.commit()
    return session


def delete_session(db: Session, user: User, session_id: uuid.UUID) -> None:
    db.delete(get_session(db, user, session_id))
    db.commit()


def recent_history(session: ChatSession, limit: int) -> list[ChatMessage]:
    usable = [message for message in session.messages if message.status != MessageStatus.FAILED]
    return [
        {
            "role": "user" if message.role is MessageRole.USER else "assistant",
            "content": message.content,
        }
        for message in usable[-limit:]
    ]


def add_question(db: Session, session: ChatSession, content: str) -> Message:
    if session.title == DEFAULT_TITLE and not session.messages:
        session.title = title_from_question(content)
    message = Message(session_id=session.id, role=MessageRole.USER, content=content)
    session.updated_at = datetime.now(UTC)
    db.add(message)
    db.commit()
    return message


def serialize_citations(answer: Answer) -> list[dict[str, Any]]:
    return [
        {
            **asdict(citation),
            "chunk_id": str(citation.chunk_id),
            "document_id": str(citation.document_id),
        }
        for citation in answer.citations
    ]


def add_answer(db: Session, session_id: uuid.UUID, answer: Answer) -> Message:
    message = Message(
        session_id=session_id,
        role=MessageRole.ASSISTANT,
        content=answer.text,
        status=MessageStatus(answer.status.value),
        citations=serialize_citations(answer),
        metrics=answer.metrics(),
    )
    db.add(message)
    touch_session(db, session_id)
    db.commit()
    return message


def add_failure(db: Session, session_id: uuid.UUID, content: str, reason: str) -> Message:
    message = Message(
        session_id=session_id,
        role=MessageRole.ASSISTANT,
        content=content,
        status=MessageStatus.FAILED,
        citations=[],
        metrics={"failure_reason": reason},
    )
    db.add(message)
    touch_session(db, session_id)
    db.commit()
    return message


def touch_session(db: Session, session_id: uuid.UUID) -> None:
    session = db.get(ChatSession, session_id)
    if session is not None:
        session.updated_at = datetime.now(UTC)


def set_feedback(db: Session, user: User, message_id: uuid.UUID, value: int | None) -> Message:
    message = db.get(Message, message_id)
    if (
        message is None
        or message.role is not MessageRole.ASSISTANT
        or message.session.user_id != user.id
    ):
        raise NotFoundError("Message not found")
    message.feedback = value
    db.commit()
    return message
