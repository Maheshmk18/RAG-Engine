import logging
import threading
import time

from app.retrieval.bm25 import BM25Index
from app.retrieval.store import ChunkStore

logger = logging.getLogger(__name__)


class LexicalIndex:
    def __init__(self, store: ChunkStore) -> None:
        self.store = store
        self._index: BM25Index[str] | None = None
        self._version: int | None = None
        self._lock = threading.Lock()

    def current(self) -> BM25Index[str]:
        version = self.store.version()
        if self._index is not None and self._version == version:
            return self._index
        with self._lock:
            if self._index is None or self._version != version:
                started = time.perf_counter()
                chunks = self.store.all_chunks()
                self._index = BM25Index([(chunk.id, chunk.contextual_text) for chunk in chunks])
                self._version = version
                logger.info(
                    "lexical index rebuilt",
                    extra={
                        "corpus_version": version,
                        "chunks": len(chunks),
                        "duration_ms": round((time.perf_counter() - started) * 1000, 1),
                    },
                )
            return self._index

    def search(self, query: str, limit: int) -> list[str]:
        return [chunk_id for chunk_id, _ in self.current().search(query, limit)]
