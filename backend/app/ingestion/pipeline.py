import logging
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.db.models import Chunk, Document, DocumentStatus
from app.ingestion.chunking import ChunkDraft, chunk_blocks
from app.ingestion.extract import ExtractionError, detect_kind, extract
from app.retrieval.embeddings import Embedder
from app.services.corpus import bump_corpus_version

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PreparedDocument:
    title: str
    drafts: list[ChunkDraft]
    embeddings: list[list[float]]
    page_count: int | None


class IngestionPipeline:
    def __init__(self, embedder: Embedder, max_words: int, overlap_words: int) -> None:
        self.embedder = embedder
        self.max_words = max_words
        self.overlap_words = overlap_words

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

    def process(self, db: Session, document_id: uuid.UUID) -> Document:
        document = db.get(Document, document_id)
        if document is None:
            raise LookupError(f"Document {document_id} no longer exists")
        started = time.perf_counter()
        prepared = self.prepare(document.title, document.filename, document.file.data)

        db.execute(delete(Chunk).where(Chunk.document_id == document.id))
        db.add_all(
            Chunk(
                document_id=document.id,
                ordinal=draft.ordinal,
                heading=draft.heading,
                page=draft.page,
                text=draft.text,
                word_count=draft.word_count,
                embedding=embedding,
            )
            for draft, embedding in zip(prepared.drafts, prepared.embeddings, strict=True)
        )
        document.title = prepared.title
        document.status = DocumentStatus.READY
        document.chunk_count = len(prepared.drafts)
        document.page_count = prepared.page_count
        document.error_message = None
        document.processed_at = datetime.now(UTC)
        bump_corpus_version(db)
        db.commit()

        logger.info(
            "document ingested",
            extra={
                "document_id": str(document.id),
                "chunks": document.chunk_count,
                "duration_ms": round((time.perf_counter() - started) * 1000, 1),
            },
        )
        return document
