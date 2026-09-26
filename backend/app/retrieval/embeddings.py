from collections.abc import Sequence
from typing import Any, Protocol

EMBEDDING_BATCH_SIZE = 64


class Embedder(Protocol):
    dimensions: int

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


class PineconeInferenceClient(Protocol):
    def embed(
        self,
        *,
        model: str,
        inputs: list[str] | str,
        parameters: dict[str, str],
    ) -> Any: ...


class PineconeEmbedder:
    def __init__(
        self, client: PineconeInferenceClient, model: str, dimensions: int
    ) -> None:
        self.client = client
        self.model = model
        self.dimensions = dimensions

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), EMBEDDING_BATCH_SIZE):
            response = self.client.embed(
                model=self.model,
                inputs=list(texts[start : start + EMBEDDING_BATCH_SIZE]),
                parameters={"input_type": "passage", "truncate": "END"},
            )
            vectors.extend(self._dense_values(response))
        self._check_dimensions(vectors)
        return vectors

    def embed_query(self, text: str) -> list[float]:
        response = self.client.embed(
            model=self.model,
            inputs=text,
            parameters={"input_type": "query", "truncate": "END"},
        )
        vectors = self._dense_values(response)
        if len(vectors) != 1:
            raise ValueError(f"Pinecone returned {len(vectors)} query embeddings, expected one")
        self._check_dimensions(vectors)
        return vectors[0]

    @staticmethod
    def _dense_values(response: Any) -> list[list[float]]:
        if response.vector_type != "dense":
            raise ValueError(
                f"Pinecone returned {response.vector_type!r} embeddings, expected dense"
            )
        return [embedding.values for embedding in response.data]

    def _check_dimensions(self, vectors: list[list[float]]) -> None:
        if any(len(vector) != self.dimensions for vector in vectors):
            actual = sorted({len(vector) for vector in vectors})
            raise ValueError(
                f"Pinecone model {self.model} returned dimensions {actual}; "
                f"expected {self.dimensions}. Match the embedding model and index dimensions."
            )
