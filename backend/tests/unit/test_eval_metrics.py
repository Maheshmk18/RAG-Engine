import pytest

from evals.metrics import contains_facts, hit, ndcg, percentile, recall, reciprocal_rank
from evals.report import evaluate_gate

RANKED = ["Leave > Booking", "Leave > Carry-Over", "Travel > Hotels", "Leave > Carry-Over"]


def test_rank_metrics() -> None:
    expected = ("Leave > Carry-Over",)
    assert hit(RANKED, expected, k=1) == 0.0
    assert hit(RANKED, expected, k=2) == 1.0
    assert reciprocal_rank(RANKED, expected) == 0.5
    assert recall(RANKED, ("Leave > Carry-Over", "Travel > Meals"), k=5) == 0.5


def test_ndcg_ignores_duplicate_hits() -> None:
    assert ndcg(["a", "b"], ("a",), k=5) == 1.0
    assert ndcg(["b", "a"], ("a",), k=5) == pytest.approx(0.6309, abs=1e-4)
    assert ndcg(["a", "a"], ("a", "b"), k=5) == pytest.approx(0.6131, abs=1e-4)


def test_fact_matching_ignores_case_spacing_and_thousands_separators() -> None:
    answer = "Claims above 1,000 need a  director's approval [2]."
    assert contains_facts(answer, ["1000", "Director"])
    assert not contains_facts(answer, ["Vice President"])


def test_percentile_interpolates() -> None:
    assert percentile([10, 20, 30, 40], 0.5) == 25.0
    assert percentile([10, 20, 30, 40], 0.95) == 38.5
    assert percentile([], 0.5) == 0.0


def test_gate_checks_floors_and_regressions() -> None:
    thresholds = {"regression_tolerance": 0.02, "retrieval": {"mrr": 0.9, "hit_rate": 0.9}}
    metrics = {"retrieval": {"mrr": 0.95, "hit_rate": 0.88}}
    baseline = {"retrieval": {"mrr": 0.99, "hit_rate": 0.88}}

    results = {result.metric: result for result in evaluate_gate(metrics, thresholds, baseline)}
    assert results["retrieval.mrr"].regressed
    assert not results["retrieval.mrr"].below_floor
    assert results["retrieval.hit_rate"].below_floor
    assert not results["retrieval.hit_rate"].regressed
    assert "down from the baseline" in results["retrieval.mrr"].describe()


def test_gate_skips_metrics_that_were_not_measured() -> None:
    thresholds = {"generation": {"faithfulness": 0.9}}
    assert evaluate_gate({"retrieval": {"mrr": 1.0}}, thresholds, None) == []
