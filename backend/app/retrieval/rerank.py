import math
import threading
from collections.abc import Sequence
from typing import Protocol

from fastembed.rerank.cross_encoder import TextCrossEncoder


class Reranker(Protocol):
    def score(self, query: str, passages: Sequence[str]) -> list[float]: ...


def sigmoid(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-value))


class CrossEncoderReranker:
    def __init__(self, model_name: str, cache_dir: str | None = None) -> None:
        self.model_name = model_name
        self.cache_dir = cache_dir
        self._model: TextCrossEncoder | None = None
        self._lock = threading.Lock()

    @property
    def model(self) -> TextCrossEncoder:
        if self._model is None:
            with self._lock:
                if self._model is None:
                    self._model = TextCrossEncoder(self.model_name, cache_dir=self.cache_dir)
        return self._model

    def score(self, query: str, passages: Sequence[str]) -> list[float]:
        if not passages:
            return []
        order = sorted(range(len(passages)), key=lambda index: len(passages[index]))
        logits = self.model.rerank(query, [passages[index] for index in order], batch_size=8)
        scores = [0.0] * len(passages)
        for index, logit in zip(order, logits, strict=True):
            scores[index] = round(sigmoid(float(logit)), 6)
        return scores
