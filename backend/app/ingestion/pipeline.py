import logging
import time
import uuid
from dataclasses import dataclass

from pymongo import ReplaceOne, ReturnDocument
from pymongo.database import Database

from app.db.mongo import CHUNKS, DOCUMENTS, utcnow
from app.db.records import DocumentRecord, DocumentStatus
from app.ingestion.chunking import ChunkDraft, chunk_blocks
from app.ingestion.extract import ExtractionError, detect_kind, extract
from app.retrieval.embeddings import Embedder
from app.retrieval.store import PineconeChunkStore
from app.services.corpus import bump_corpus_version
from app.services.documents import read_file

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PreparedDocument:
    title: str
    drafts: list[ChunkDraft]
    embeddings: list[list[float]]
    page_count: int | None


class IngestionPipeline:
    def __init__(
        self,
        embedder: Embedder,
        max_words: int,
        overlap_words: int,
        vector_store: PineconeChunkStore | None = None,
    ) -> None:
        self.embedder = embedder
        self.max_words = max_words
        self.overlap_words = overlap_words
        self.vector_store = vector_store

    def prepare(self, title: str, filename: str, data: bytes) -> PreparedDocument:
        kind = detect_kind(filename)
        if kind is None:
            raise ExtractionError(f"Unsupported file type for {filename}")
        extracted = extract(kind, data)
        title = extracted.title or title
        drafts = chunk_blocks(extracted.blocks, self.max_words, self.overlap_words)
        embeddings = self.embedder.embed_documents(
            [draft.contextual_text(title) for draft in drafts]
        )
        return PreparedDocument(title, drafts, embeddings, extracted.page_count)

    def process(self, db: Database, document_id: str) -> DocumentRecord:
        if self.vector_store is None:
            raise RuntimeError("Pinecone vector storage is required to process documents")
        raw = db[DOCUMENTS].find_one({"_id": document_id})
        if raw is None:
            raise LookupError(f"Document {document_id} no longer exists")
        document = DocumentRecord.from_mongo(raw)
        started = time.perf_counter()
        prepared = self.prepare(document.title, document.filename, read_file(db, document))

        old_ids = [raw["_id"] for raw in db[CHUNKS].find({"document_id": document.id}, {"_id": 1})]
        chunk_records = [
            {
                "_id": str(uuid.uuid5(uuid.UUID(document.id), str(draft.ordinal))),
                "document_id": document.id,
                "document_title": prepared.title,
                "ordinal": draft.ordinal,
                "heading": draft.heading,
                "page": draft.page,
                "text": draft.text,
                "word_count": draft.word_count,
            }
            for draft in prepared.drafts
        ]
        new_ids = [record["_id"] for record in chunk_records]
        self.vector_store.upsert_vectors(new_ids, prepared.embeddings)
        if chunk_records:
            db[CHUNKS].bulk_write(
                [
                    ReplaceOne({"_id": record["_id"]}, record, upsert=True)
                    for record in chunk_records
                ]
            )
        new_id_set = set(new_ids)
        stale_ids = [chunk_id for chunk_id in old_ids if chunk_id not in new_id_set]
        if stale_ids:
            db[CHUNKS].delete_many({"_id": {"$in": stale_ids}})
            self.vector_store.delete_vectors(stale_ids)
        now = utcnow()
        updated = db[DOCUMENTS].find_one_and_update(
            {"_id": document.id},
            {
                "$set": {
                    "title": prepared.title,
                    "status": DocumentStatus.READY.value,
                    "chunk_count": len(prepared.drafts),
                    "page_count": prepared.page_count,
                    "error_message": None,
                    "processed_at": now,
                    "updated_at": now,
                }
            },
            return_document=ReturnDocument.AFTER,
        )
        bump_corpus_version(db)

        logger.info(
            "document ingested",
            extra={
                "document_id": document.id,
                "chunks": len(prepared.drafts),
                "duration_ms": round((time.perf_counter() - started) * 1000, 1),
            },
        )
        return DocumentRecord.from_mongo(updated or raw)
