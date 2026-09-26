from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Protocol

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


class PineconeIndexClient(Protocol):
    def upsert(self, *, vectors: list[dict[str, Any]], namespace: str) -> Any: ...

    def query(
        self,
        *,
        vector: list[float],
        top_k: int,
        namespace: str,
        include_metadata: bool = False,
    ) -> Any: ...

    def delete(self, *, ids: list[str], namespace: str) -> Any: ...


class PineconeChunkStore:
    def __init__(
        self,
        db: Database,
        index: PineconeIndexClient,
        namespace: str,
    ) -> None:
        self.db = db
        self.index = index
        self.namespace = namespace

    def version(self) -> int:
        return current_corpus_version(self.db)

    def all_chunks(self) -> list[ChunkRecord]:
        return [ChunkRecord.from_mongo(raw) for raw in self.db[CHUNKS].find({}, RECORD_FIELDS)]

    def upsert_vectors(self, ids: Sequence[str], embeddings: Sequence[Sequence[float]]) -> None:
        if len(ids) != len(embeddings):
            raise ValueError("Pinecone vector IDs and embeddings must have the same length")
        for start in range(0, len(ids), 100):
            batch = [
                {"id": ids[index], "values": list(embeddings[index])}
                for index in range(start, min(start + 100, len(ids)))
            ]
            response = self.index.upsert(vectors=batch, namespace=self.namespace)
            if response.upserted_count != len(batch):
                raise RuntimeError(
                    f"Pinecone upserted {response.upserted_count} of {len(batch)} vectors"
                )

    def delete_vectors(self, ids: Sequence[str]) -> None:
        for start in range(0, len(ids), 1000):
            self.index.delete(ids=list(ids[start : start + 1000]), namespace=self.namespace)

    def vector_search(self, embedding: Sequence[float], limit: int) -> list[str]:
        if limit <= 0:
            return []
        response = self.index.query(
            vector=list(embedding),
            top_k=limit,
            namespace=self.namespace,
            include_metadata=False,
        )
        return [match.id for match in response.matches]

    def get_many(self, ids: Sequence[str]) -> dict[str, ChunkRecord]:
        if not ids:
            return {}
        cursor = self.db[CHUNKS].find({"_id": {"$in": list(ids)}}, RECORD_FIELDS)
        return {raw["_id"]: ChunkRecord.from_mongo(raw) for raw in cursor}
