from types import SimpleNamespace
from typing import Any, cast

from pymongo.database import Database

from app.retrieval.store import PineconeChunkStore


class RecordingIndex:
    def __init__(self) -> None:
        self.query_args: dict[str, Any] = {}

    def query(self, **kwargs: Any) -> SimpleNamespace:
        self.query_args = kwargs
        return SimpleNamespace(
            matches=[SimpleNamespace(id="chunk-b"), SimpleNamespace(id="chunk-a")]
        )


def test_pinecone_search_sends_vector_namespace_and_limit() -> None:
    index = RecordingIndex()
    store = PineconeChunkStore(cast(Database, object()), cast(Any, index), "enterprise-rag")

    assert store.vector_search([0.1, 0.2, 0.3], limit=5) == ["chunk-b", "chunk-a"]
    assert index.query_args == {
        "vector": [0.1, 0.2, 0.3],
        "top_k": 5,
        "namespace": "enterprise-rag",
        "include_metadata": False,
    }
