import logging
from datetime import UTC, datetime

from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.database import Database
from pymongo.operations import IndexModel, SearchIndexModel

from app.core.config import Settings

logger = logging.getLogger(__name__)

EMBEDDING_DIMENSIONS = 384

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


def ensure_vector_index(db: Database, name: str) -> None:
    existing = {index["name"] for index in db[CHUNKS].list_search_indexes()}
    if name in existing:
        return
    definition = {
        "fields": [
            {
                "type": "vector",
                "path": "embedding",
                "numDimensions": EMBEDDING_DIMENSIONS,
                "similarity": "cosine",
            }
        ]
    }
    db[CHUNKS].create_search_index(
        SearchIndexModel(definition=definition, name=name, type="vectorSearch")
    )
    logger.info("vector search index requested", extra={"index": name})


def ensure_indexes(db: Database, settings: Settings) -> None:
    for collection, indexes in INDEXES.items():
        db[collection].create_indexes(indexes)
    if settings.vector_search == "atlas":
        ensure_vector_index(db, settings.atlas_vector_index)
