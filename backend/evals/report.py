import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class GateResult:
    metric: str
    value: float
    floor: float | None
    baseline: float | None
    tolerance: float

    @property
    def below_floor(self) -> bool:
        return self.floor is not None and self.value < self.floor

    @property
    def regressed(self) -> bool:
        return self.baseline is not None and self.value < self.baseline - self.tolerance

    @property
    def passed(self) -> bool:
        return not self.below_floor and not self.regressed

    def describe(self) -> str:
        if self.below_floor:
            return f"{self.metric} is {self.value:.3f}, below the floor of {self.floor:.3f}"
        if self.regressed:
            return (
                f"{self.metric} is {self.value:.3f}, down from the baseline of "
                f"{self.baseline:.3f} by more than {self.tolerance:.3f}"
            )
        return f"{self.metric} is {self.value:.3f}"


def load_thresholds(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def lookup(metrics: dict[str, Any], dotted: str) -> float | None:
    node: Any = metrics
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return float(node) if isinstance(node, int | float) else None


def evaluate_gate(
    metrics: dict[str, Any], thresholds: dict[str, Any], baseline: dict[str, Any] | None
) -> list[GateResult]:
    tolerance = float(thresholds.get("regression_tolerance", 0.0))
    results = []
    for section, floors in thresholds.items():
        if not isinstance(floors, dict):
            continue
        for name, floor in floors.items():
            metric = f"{section}.{name}"
            value = lookup(metrics, metric)
            if value is None:
                continue
            previous = lookup(baseline, metric) if baseline else None
            results.append(GateResult(metric, value, float(floor), previous, tolerance))
    return results


def format_value(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.3f}"


def markdown_summary(report: dict[str, Any], gate: list[GateResult]) -> str:
    lines = [
        f"## Evaluation: {report['suite']} suite",
        "",
        f"{report['cases']} questions, corpus of {report['corpus']['chunks']} chunks from "
        f"{report['corpus']['documents']} documents.",
        "",
        "| Metric | Value | Floor | Baseline | Status |",
        "| --- | --- | --- | --- | --- |",
    ]
    for result in gate:
        status = "pass" if result.passed else "FAIL"
        lines.append(
            f"| {result.metric} | {result.value:.3f} | {format_value(result.floor)} "
            f"| {format_value(result.baseline)} | {status} |"
        )

    ablation = report["metrics"].get("ablation")
    if ablation:
        lines += [
            "",
            "### Retrieval ablation (top 5)",
            "",
            "| Strategy | Hit rate | Recall | MRR | nDCG |",
            "| --- | --- | --- | --- | --- |",
        ]
        for strategy, values in ablation.items():
            lines.append(
                f"| {strategy} | {values['hit_rate']:.3f} | {values['recall']:.3f} "
                f"| {values['mrr']:.3f} | {values['ndcg']:.3f} |"
            )

    latency = report["metrics"].get("latency")
    if latency:
        lines += ["", "### Latency (ms)", "", "| Stage | p50 | p95 |", "| --- | --- | --- |"]
        for stage, values in latency.items():
            lines.append(f"| {stage} | {values['p50']} | {values['p95']} |")
    return "\n".join(lines) + "\n"
