import uuid
from dataclasses import asdict
from typing import Any

from pymongo import ASCENDING, DESCENDING
from pymongo.database import Database

from app.core.errors import NotFoundError
from app.db.mongo import MESSAGES, SESSIONS, utcnow
from app.db.records import MessageRecord, MessageRole, MessageStatus, SessionRecord
from app.generation.answerer import Answer
from app.generation.llm import ChatMessage

DEFAULT_TITLE = "New conversation"
TITLE_LENGTH = 60


def title_from_question(question: str) -> str:
    text = " ".join(question.split())
    if len(text) <= TITLE_LENGTH:
        return text
    return text[:TITLE_LENGTH].rsplit(" ", 1)[0] + "..."


def list_sessions(db: Database, client_id: str, limit: int = 100) -> list[SessionRecord]:
    cursor = db[SESSIONS].find({"client_id": client_id}).sort("updated_at", DESCENDING).limit(limit)
    return [SessionRecord.from_mongo(raw) for raw in cursor]


def create_session(db: Database, client_id: str, title: str | None = None) -> SessionRecord:
    now = utcnow()
    raw = {
        "_id": str(uuid.uuid4()),
        "client_id": client_id,
        "title": title or DEFAULT_TITLE,
        "created_at": now,
        "updated_at": now,
    }
    db[SESSIONS].insert_one(raw)
    return SessionRecord.from_mongo(raw)


def get_session(db: Database, client_id: str, session_id: str) -> SessionRecord:
    raw = db[SESSIONS].find_one({"_id": session_id, "client_id": client_id})
    if raw is None:
        raise NotFoundError("Conversation not found")
    return SessionRecord.from_mongo(raw)


def list_messages(db: Database, session_id: str) -> list[MessageRecord]:
    cursor = db[MESSAGES].find({"session_id": session_id}).sort("created_at", ASCENDING)
    return [MessageRecord.from_mongo(raw) for raw in cursor]


def rename_session(db: Database, client_id: str, session_id: str, title: str) -> SessionRecord:
    get_session(db, client_id, session_id)
    db[SESSIONS].update_one({"_id": session_id}, {"$set": {"title": title}})
    return get_session(db, client_id, session_id)


def delete_session(db: Database, client_id: str, session_id: str) -> None:
    get_session(db, client_id, session_id)
    db[MESSAGES].delete_many({"session_id": session_id})
    db[SESSIONS].delete_one({"_id": session_id})


def recent_history(messages: list[MessageRecord], limit: int) -> list[ChatMessage]:
    usable = [message for message in messages if message.status != MessageStatus.FAILED]
    return [
        {
            "role": "user" if message.role is MessageRole.USER else "assistant",
            "content": message.content,
        }
        for message in usable[-limit:]
    ]


def save_message(db: Database, message: MessageRecord) -> MessageRecord:
    db[MESSAGES].insert_one(message.to_mongo())
    db[SESSIONS].update_one({"_id": message.session_id}, {"$set": {"updated_at": utcnow()}})
    return message


def add_question(db: Database, session: SessionRecord, content: str, first: bool) -> MessageRecord:
    if first and session.title == DEFAULT_TITLE:
        db[SESSIONS].update_one(
            {"_id": session.id}, {"$set": {"title": title_from_question(content)}}
        )
    return save_message(
        db,
        MessageRecord(
            id=str(uuid.uuid4()),
            session_id=session.id,
            role=MessageRole.USER,
            content=content,
            created_at=utcnow(),
        ),
    )


def serialize_citations(answer: Answer) -> list[dict[str, Any]]:
    return [asdict(citation) for citation in answer.citations]


def add_answer(db: Database, session_id: str, answer: Answer) -> MessageRecord:
    return save_message(
        db,
        MessageRecord(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=answer.text,
            created_at=utcnow(),
            status=MessageStatus(answer.status.value),
            citations=serialize_citations(answer),
            metrics=answer.metrics(),
        ),
    )


def add_failure(db: Database, session_id: str, content: str, reason: str) -> MessageRecord:
    return save_message(
        db,
        MessageRecord(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=content,
            created_at=utcnow(),
            status=MessageStatus.FAILED,
            metrics={"failure_reason": reason},
        ),
    )


def set_feedback(db: Database, client_id: str, message_id: str, value: int | None) -> MessageRecord:
    raw = db[MESSAGES].find_one({"_id": message_id, "role": MessageRole.ASSISTANT.value})
    if raw is None:
        raise NotFoundError("Message not found")
    if db[SESSIONS].count_documents({"_id": raw["session_id"], "client_id": client_id}) == 0:
        raise NotFoundError("Message not found")
    db[MESSAGES].update_one({"_id": message_id}, {"$set": {"feedback": value}})
    raw["feedback"] = value
    return MessageRecord.from_mongo(raw)
