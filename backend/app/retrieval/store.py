import threading
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Literal, Protocol

import numpy as np
from pymongo.database import Database

from app.db.mongo import CHUNKS
from app.ingestion.chunking import contextual_text
from app.services.corpus import current_corpus_version

RECORD_FIELDS = {"document_id": 1, "document_title": 1, "heading": 1, "page": 1, "text": 1}


@dataclass(frozen=True)
class ChunkRecord:
    id: str
    document_id: str
    document_title: str
    heading: str | None
    page: int | None
    text: str

    @property
    def contextual_text(self) -> str:
        return contextual_text(self.document_title, self.heading, self.text)

    @classmethod
    def from_mongo(cls, raw: dict[str, Any]) -> "ChunkRecord":
        return cls(
            id=raw["_id"],
            document_id=raw["document_id"],
            document_title=raw["document_title"],
            heading=raw.get("heading"),
            page=raw.get("page"),
            text=raw["text"],
        )


class ChunkStore(Protocol):
    def version(self) -> int: ...

    def all_chunks(self) -> list[ChunkRecord]: ...

    def vector_search(self, embedding: Sequence[float], limit: int) -> list[str]: ...

    def get_many(self, ids: Sequence[str]) -> dict[str, ChunkRecord]: ...


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

    def vector_search(self, embedding: Sequence[float], limit: int) -> list[str]:
        if not self.ids:
            return []
        query = np.asarray(embedding, dtype=np.float32)
        similarities = self.matrix @ (query / (np.linalg.norm(query) or 1.0))
        order = np.argsort(-similarities)[:limit]
        return [self.ids[index] for index in order]

    def get_many(self, ids: Sequence[str]) -> dict[str, ChunkRecord]:
        return {chunk_id: self.records[chunk_id] for chunk_id in ids if chunk_id in self.records}


class MongoChunkStore:
    def __init__(
        self,
        db: Database,
        mode: Literal["local", "atlas"] = "local",
        atlas_index: str = "chunk_embeddings",
    ) -> None:
        self.db = db
        self.mode = mode
        self.atlas_index = atlas_index
        self._snapshot: InMemoryChunkStore | None = None
        self._snapshot_version: int | None = None
        self._lock = threading.Lock()

    def version(self) -> int:
        return current_corpus_version(self.db)

    def all_chunks(self) -> list[ChunkRecord]:
        return [ChunkRecord.from_mongo(raw) for raw in self.db[CHUNKS].find({}, RECORD_FIELDS)]

    def snapshot(self) -> InMemoryChunkStore:
        version = self.version()
        if self._snapshot is not None and self._snapshot_version == version:
            return self._snapshot
        with self._lock:
            if self._snapshot is None or self._snapshot_version != version:
                raws = list(self.db[CHUNKS].find({}, {**RECORD_FIELDS, "embedding": 1}))
                self._snapshot = InMemoryChunkStore(
                    [ChunkRecord.from_mongo(raw) for raw in raws],
                    [raw["embedding"] for raw in raws],
                )
                self._snapshot_version = version
            return self._snapshot

    def vector_search(self, embedding: Sequence[float], limit: int) -> list[str]:
        if self.mode == "local":
            return self.snapshot().vector_search(embedding, limit)
        pipeline: list[dict[str, Any]] = [
            {
                "$vectorSearch": {
                    "index": self.atlas_index,
                    "path": "embedding",
                    "queryVector": list(embedding),
                    "numCandidates": max(limit * 10, 100),
                    "limit": limit,
                }
            },
            {"$project": {"_id": 1}},
        ]
        return [raw["_id"] for raw in self.db[CHUNKS].aggregate(pipeline)]

    def get_many(self, ids: Sequence[str]) -> dict[str, ChunkRecord]:
        if not ids:
            return {}
        cursor = self.db[CHUNKS].find({"_id": {"$in": list(ids)}}, RECORD_FIELDS)
        return {raw["_id"]: ChunkRecord.from_mongo(raw) for raw in cursor}
