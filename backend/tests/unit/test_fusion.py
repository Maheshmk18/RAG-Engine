import pytest

from app.retrieval.fusion import reciprocal_rank_fusion


def test_scores_follow_the_rrf_formula() -> None:
    fused = dict(reciprocal_rank_fusion([["a", "b"], ["b", "c"]], k=60))
    assert fused["a"] == pytest.approx(1 / 61)
    assert fused["b"] == pytest.approx(1 / 62 + 1 / 61)
    assert fused["c"] == pytest.approx(1 / 62)


def test_agreement_between_rankings_wins() -> None:
    fused = reciprocal_rank_fusion([["only-dense", "shared"], ["only-lexical", "shared"]])
    assert fused[0][0] == "shared"


def test_empty_rankings() -> None:
    assert reciprocal_rank_fusion([[], []]) == []
