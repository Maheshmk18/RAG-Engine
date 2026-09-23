import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

import numpy as np
from sqlalchemy import select, text

from app.db.models import Chunk, Document
from app.db.session import SessionFactory
from app.ingestion.chunking import contextual_text
from app.services.corpus import current_corpus_version


@dataclass(frozen=True)
class ChunkRecord:
    id: uuid.UUID
    document_id: uuid.UUID
    document_title: str
    heading: str | None
    page: int | None
    text: str

    @property
    def contextual_text(self) -> str:
        return contextual_text(self.document_title, self.heading, self.text)


class ChunkStore(Protocol):
    def version(self) -> int: ...

    def all_chunks(self) -> list[ChunkRecord]: ...

    def vector_search(self, embedding: Sequence[float], limit: int) -> list[uuid.UUID]: ...

    def get_many(self, ids: Sequence[uuid.UUID]) -> dict[uuid.UUID, ChunkRecord]: ...


RECORD_COLUMNS = (
    Chunk.id,
    Chunk.document_id,
    Document.title,
    Chunk.heading,
    Chunk.page,
    Chunk.text,
)


class PostgresChunkStore:
    def __init__(self, session_factory: SessionFactory, ef_search: int = 100) -> None:
        self.session_factory = session_factory
        self.ef_search = int(ef_search)

    def version(self) -> int:
        with self.session_factory() as db:
            return current_corpus_version(db)

    def all_chunks(self) -> list[ChunkRecord]:
        query = select(*RECORD_COLUMNS).join(Document, Document.id == Chunk.document_id)
        with self.session_factory() as db:
            return [ChunkRecord(*row) for row in db.execute(query)]

    def vector_search(self, embedding: Sequence[float], limit: int) -> list[uuid.UUID]:
        distance = Chunk.embedding.cosine_distance(list(embedding))
        query = select(Chunk.id).order_by(distance).limit(limit)
        with self.session_factory() as db, db.begin():
            db.execute(text(f"SET LOCAL hnsw.ef_search = {self.ef_search}"))
            return list(db.scalars(query))

    def get_many(self, ids: Sequence[uuid.UUID]) -> dict[uuid.UUID, ChunkRecord]:
        if not ids:
            return {}
        query = (
            select(*RECORD_COLUMNS)
            .join(Document, Document.id == Chunk.document_id)
            .where(Chunk.id.in_(ids))
        )
        with self.session_factory() as db:
            return {row[0]: ChunkRecord(*row) for row in db.execute(query)}


class InMemoryChunkStore:
    def __init__(self, records: Sequence[ChunkRecord], embeddings: Sequence[Sequence[float]]):
        self.records = {record.id: record for record in records}
        self.ids = [record.id for record in records]
        matrix = np.asarray(embeddings, dtype=np.float32).reshape(len(records), -1)
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        self.matrix = matrix / np.where(norms == 0, 1, norms)

    def version(self) -> int:
        return 1

    def all_chunks(self) -> list[ChunkRecord]:
        return list(self.records.values())

    def vector_search(self, embedding: Sequence[float], limit: int) -> list[uuid.UUID]:
        if not self.ids:
            return []
        query = np.asarray(embedding, dtype=np.float32)
        similarities = self.matrix @ (query / (np.linalg.norm(query) or 1.0))
        order = np.argsort(-similarities)[:limit]
        return [self.ids[index] for index in order]

    def get_many(self, ids: Sequence[uuid.UUID]) -> dict[uuid.UUID, ChunkRecord]:
        return {chunk_id: self.records[chunk_id] for chunk_id in ids if chunk_id in self.records}
