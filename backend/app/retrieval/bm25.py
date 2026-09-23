import heapq
import math
import re
from collections import Counter, defaultdict
from collections.abc import Hashable, Sequence
from typing import Generic, TypeVar

Key = TypeVar("Key", bound=Hashable)

TOKEN = re.compile(r"[a-z0-9]+")

STOP_WORDS = frozenset(
    (
        "a about above after again all am an and any are as at be because been before being "
        "below between both but by can could did do does doing down during each few for from "
        "further had has have having he her here hers him his how i if in into is it its "
        "itself just me more most my no nor not now of off on once only or other our ours "
        "out over own same she should so some such than that the their theirs them then "
        "there these they this those through to too under until up very was we were what "
        "when where which while who whom why will with would you your yours"
    ).split()
)


def stem(token: str) -> str:
    if len(token) > 5 and token.endswith("ing"):
        return token[:-3]
    if len(token) > 4 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 4 and token.endswith("ed"):
        return token[:-2]
    if len(token) > 3 and token.endswith("s") and not token.endswith(("ss", "us", "is")):
        return token[:-1]
    return token


def tokenize(text: str) -> list[str]:
    return [stem(token) for token in TOKEN.findall(text.lower()) if token not in STOP_WORDS]


class BM25Index(Generic[Key]):
    def __init__(self, documents: Sequence[tuple[Key, str]], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.keys: list[Key] = [key for key, _ in documents]
        self.lengths: list[int] = []
        self.postings: defaultdict[str, list[tuple[int, int]]] = defaultdict(list)
        for position, (_, text) in enumerate(documents):
            frequencies = Counter(tokenize(text))
            self.lengths.append(sum(frequencies.values()))
            for term, frequency in frequencies.items():
                self.postings[term].append((position, frequency))
        self.average_length = (sum(self.lengths) / len(self.lengths)) if self.lengths else 0.0
        count = len(self.keys)
        self.idf = {
            term: math.log(1 + (count - len(entries) + 0.5) / (len(entries) + 0.5))
            for term, entries in self.postings.items()
        }

    def __len__(self) -> int:
        return len(self.keys)

    def search(self, query: str, limit: int) -> list[tuple[Key, float]]:
        scores: defaultdict[int, float] = defaultdict(float)
        for term in set(tokenize(query)):
            idf = self.idf.get(term)
            if idf is None:
                continue
            for position, frequency in self.postings[term]:
                norm = 1 - self.b + self.b * self.lengths[position] / self.average_length
                scores[position] += idf * frequency * (self.k1 + 1) / (frequency + self.k1 * norm)
        best = heapq.nlargest(limit, scores.items(), key=lambda item: item[1])
        return [(self.keys[position], score) for position, score in best]
