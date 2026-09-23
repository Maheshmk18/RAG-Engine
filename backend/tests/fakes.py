import hashlib
import math
import re
from collections.abc import Sequence

from app.db.models import EMBEDDING_DIMENSIONS

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
