from datetime import UTC, datetime

from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.database import Database
from pymongo.operations import IndexModel

from app.core.config import Settings

DOCUMENTS = "documents"
CHUNKS = "chunks"
SESSIONS = "chat_sessions"
MESSAGES = "chat_messages"
CORPUS = "corpus_state"
FILES = "document_files"

INDEXES: dict[str, list[IndexModel]] = {
    DOCUMENTS: [
        IndexModel([("sha256", ASCENDING)], unique=True),
        IndexModel([("status", ASCENDING), ("created_at", ASCENDING)]),
        IndexModel([("created_at", DESCENDING)]),
    ],
    CHUNKS: [
        IndexModel([("document_id", ASCENDING), ("ordinal", ASCENDING)], unique=True),
    ],
    SESSIONS: [
        IndexModel([("client_id", ASCENDING), ("updated_at", DESCENDING)]),
    ],
    MESSAGES: [
        IndexModel([("session_id", ASCENDING), ("created_at", ASCENDING)]),
    ],
}


def utcnow() -> datetime:
    return datetime.now(UTC)


def create_client(settings: Settings) -> MongoClient:
    return MongoClient(
        settings.mongodb_url,
        tz_aware=True,
        appname="enterprise-rag",
        serverSelectionTimeoutMS=5000,
    )


def ensure_indexes(db: Database) -> None:
    for collection, indexes in INDEXES.items():
        db[collection].create_indexes(indexes)
