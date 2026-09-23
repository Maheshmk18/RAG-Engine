import hashlib
import math
import re
from collections.abc import Iterator, Sequence

from app.db.mongo import EMBEDDING_DIMENSIONS
from app.generation.llm import ChatMessage, Completion, Usage
from app.retrieval.bm25 import tokenize

TOKEN = re.compile(r"[a-z0-9]+")


class HashingEmbedder:
    dimensions = EMBEDDING_DIMENSIONS

    def _vector(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in TOKEN.findall(text.lower()):
            bucket = int(hashlib.md5(token.encode()).hexdigest(), 16) % self.dimensions
            vector[bucket] += 1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._vector(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vector(text)


class OverlapReranker:
    def score(self, query: str, passages: Sequence[str]) -> list[float]:
        terms = set(tokenize(query))
        return [
            round(len(terms & set(tokenize(passage))) / len(terms), 6) if terms else 0.0
            for passage in passages
        ]


class ScriptedLLM:
    def __init__(
        self,
        answers: Sequence[str] = (),
        completions: Sequence[str] = (),
        failure: Exception | None = None,
    ) -> None:
        self.answers = list(answers)
        self.completions = list(completions)
        self.failure = failure
        self.calls: list[tuple[str, list[ChatMessage]]] = []

    def complete(
        self, messages: list[ChatMessage], *, model: str, temperature: float, max_tokens: int
    ) -> Completion:
        self.calls.append(("complete", messages))
        if self.failure:
            raise self.failure
        return Completion(self.completions.pop(0), model, Usage(100, 20))

    def stream(
        self, messages: list[ChatMessage], *, model: str, temperature: float, max_tokens: int
    ) -> Iterator[str | Completion]:
        self.calls.append(("stream", messages))
        if self.failure:
            raise self.failure
        text = self.answers.pop(0)
        words = text.split(" ")
        for index, word in enumerate(words):
            yield word if index == len(words) - 1 else word + " "
        yield Completion(text, model, Usage(400, len(words)))
