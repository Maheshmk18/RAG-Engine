from typing import Any, cast

from pymongo.database import Database

from app.retrieval.store import MongoChunkStore


class RecordingCollection:
    def __init__(self) -> None:
        self.pipelines: list[list[dict[str, Any]]] = []

    def aggregate(self, pipeline: list[dict[str, Any]]) -> list[dict[str, Any]]:
        self.pipelines.append(pipeline)
        return [{"_id": "chunk-b"}, {"_id": "chunk-a"}]


class RecordingDatabase:
    def __init__(self) -> None:
        self.chunks = RecordingCollection()

    def __getitem__(self, name: str) -> RecordingCollection:
        assert name == "chunks"
        return self.chunks


def test_atlas_mode_uses_vector_search_stage() -> None:
    db = RecordingDatabase()
    store = MongoChunkStore(cast(Database, db), mode="atlas", atlas_index="chunk_embeddings")

    assert store.vector_search([0.1, 0.2, 0.3], limit=5) == ["chunk-b", "chunk-a"]
    stage = db.chunks.pipelines[0][0]["$vectorSearch"]
    assert stage["index"] == "chunk_embeddings"
    assert stage["path"] == "embedding"
    assert stage["queryVector"] == [0.1, 0.2, 0.3]
    assert stage["limit"] == 5
    assert stage["numCandidates"] == 100
