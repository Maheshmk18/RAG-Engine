import math
import re
from collections.abc import Sequence
from statistics import mean

NUMBER_SEPARATOR = re.compile(r"(?<=\d),(?=\d{3})")


def first_relevant_rank(ranked: Sequence[str], expected: Sequence[str]) -> int | None:
    for rank, key in enumerate(ranked, start=1):
        if key in expected:
            return rank
    return None


def hit(ranked: Sequence[str], expected: Sequence[str], k: int) -> float:
    return 1.0 if first_relevant_rank(ranked[:k], expected) else 0.0


def recall(ranked: Sequence[str], expected: Sequence[str], k: int) -> float:
    found = set(ranked[:k]) & set(expected)
    return len(found) / len(set(expected))


def reciprocal_rank(ranked: Sequence[str], expected: Sequence[str]) -> float:
    rank = first_relevant_rank(ranked, expected)
    return 1.0 / rank if rank else 0.0


def ndcg(ranked: Sequence[str], expected: Sequence[str], k: int) -> float:
    seen: set[str] = set()
    gains = []
    for key in ranked[:k]:
        gains.append(1.0 if key in expected and key not in seen else 0.0)
        seen.add(key)
    dcg = sum(gain / math.log2(position + 2) for position, gain in enumerate(gains))
    ideal = sum(1.0 / math.log2(position + 2) for position in range(min(k, len(set(expected)))))
    return dcg / ideal if ideal else 0.0


def normalize(text: str) -> str:
    return " ".join(NUMBER_SEPARATOR.sub("", text).lower().split())


def contains_facts(answer: str, facts: Sequence[str]) -> bool:
    haystack = normalize(answer)
    return all(normalize(fact) in haystack for fact in facts)


def percentile(values: Sequence[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower, upper = math.floor(position), math.ceil(position)
    blended = ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)
    return round(blended, 1)


def average(values: Sequence[float]) -> float:
    return round(mean(values), 4) if values else 0.0
