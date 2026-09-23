from collections import defaultdict
from collections.abc import Hashable, Sequence
from typing import TypeVar

Key = TypeVar("Key", bound=Hashable)


def reciprocal_rank_fusion(
    rankings: Sequence[Sequence[Key]], k: int = 60
) -> list[tuple[Key, float]]:
    scores: defaultdict[Key, float] = defaultdict(float)
    for ranking in rankings:
        for rank, key in enumerate(ranking, start=1):
            scores[key] += 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda item: item[1], reverse=True)
