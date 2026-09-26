from collections import defaultdict
from collections.abc import Hashable, Sequence
from typing import TypeVar

Key = TypeVar("Key", bound=Hashable)


def reciprocal_rank_fusion(
    rankings: Sequence[Sequence[Key]],
    k: int = 60,
    weights: Sequence[float] | None = None,
) -> list[tuple[Key, float]]:
    scores: defaultdict[Key, float] = defaultdict(float)
    ranking_weights = weights or [1.0] * len(rankings)
    if len(ranking_weights) != len(rankings):
        raise ValueError("Each ranking must have a corresponding weight")
    for ranking, weight in zip(rankings, ranking_weights, strict=True):
        for rank, key in enumerate(ranking, start=1):
            scores[key] += weight / (k + rank)
    return sorted(scores.items(), key=lambda item: item[1], reverse=True)
