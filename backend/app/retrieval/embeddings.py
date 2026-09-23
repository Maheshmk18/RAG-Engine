import threading
from collections.abc import Sequence
from typing import Protocol

from fastembed import TextEmbedding


class Embedder(Protocol):
    dimensions: int

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


class FastEmbedEmbedder:
    def __init__(self, model_name: str, dimensions: int, cache_dir: str | None = None) -> None:
        self.model_name = model_name
        self.dimensions = dimensions
        self.cache_dir = cache_dir
        self._model: TextEmbedding | None = None
        self._lock = threading.Lock()

    @property
    def model(self) -> TextEmbedding:
        if self._model is None:
            with self._lock:
                if self._model is None:
                    self._model = TextEmbedding(self.model_name, cache_dir=self.cache_dir)
        return self._model

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        vectors = [vector.tolist() for vector in self.model.embed(list(texts), batch_size=32)]
        self._check_dimensions(vectors)
        return vectors

    def embed_query(self, text: str) -> list[float]:
        vector: list[float] = next(iter(self.model.query_embed(text))).tolist()
        self._check_dimensions([vector])
        return vector

    def _check_dimensions(self, vectors: list[list[float]]) -> None:
        if vectors and len(vectors[0]) != self.dimensions:
            raise ValueError(
                f"{self.model_name} produced {len(vectors[0])} dimensions, "
                f"expected {self.dimensions}"
            )
