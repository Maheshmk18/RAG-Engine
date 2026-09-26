import argparse
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.core.config import Settings
from app.core.logging import configure_logging
from app.generation.answerer import AnswerService, AnswerStatus
from app.generation.llm import GroqClient
from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.retriever import HybridRetriever
from app.retrieval.store import InMemoryChunkStore
from app.runtime import (
    answer_config,
    build_embedder,
    build_pipeline,
    build_reranker,
    build_retriever,
)
from app.telemetry.tracing import Trace
from evals.dataset import EvalCase, build_corpus, load_cases, section_key
from evals.judge import FaithfulnessJudge
from evals.metrics import average, contains_facts, hit, ndcg, percentile, recall, reciprocal_rank
from evals.report import evaluate_gate, load_thresholds, markdown_summary

HERE = Path(__file__).resolve().parent
TOP_K = 5


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="python -m evals.run")
    parser.add_argument("--suite", choices=["retrieval", "full"], default="retrieval")
    parser.add_argument("--dataset", type=Path, default=HERE / "dataset.jsonl")
    parser.add_argument("--corpus", type=Path, default=HERE.parents[1] / "knowledge_base")
    parser.add_argument("--thresholds", type=Path, default=HERE / "thresholds.toml")
    parser.add_argument("--baseline", type=Path, default=HERE / "baseline.json")
    parser.add_argument("--output", type=Path, default=HERE / "reports" / "latest.json")
    parser.add_argument("--judge-model", default="qwen/qwen3.8-27b")
    parser.add_argument("--update-baseline", action="store_true")
    parser.add_argument("--limit", type=int)
    return parser.parse_args(argv)


def progress(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def git_revision() -> str | None:
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def strategy_rankings(
    case: EvalCase, retriever: HybridRetriever, store: InMemoryChunkStore
) -> tuple[dict[str, list[str]], Trace, int]:
    config = retriever.config
    trace = Trace()
    result = retriever.retrieve(case.question, trace)
    dense = store.vector_search(
        retriever.embedder.embed_query(case.question), config.dense_candidates
    )
    lexical = retriever.lexical.search(case.question, config.lexical_candidates)
    hybrid = [chunk_id for chunk_id, _ in reciprocal_rank_fusion([dense, lexical], config.rrf_k)]

    def keys(ids: list[Any]) -> list[str]:
        return [section_key(store.records[chunk_id]) for chunk_id in ids[:TOP_K]]

    rankings = {
        "dense": keys(dense),
        "bm25": keys(lexical),
        "hybrid": keys(hybrid),
        "hybrid_rerank": [section_key(passage.chunk) for passage in result.passages],
    }
    return rankings, trace, len(result.passages)


def score_rankings(ranked: list[str], expected: tuple[str, ...]) -> dict[str, float]:
    return {
        "hit_rate": hit(ranked, expected, TOP_K),
        "recall": recall(ranked, expected, TOP_K),
        "mrr": reciprocal_rank(ranked, expected),
        "ndcg": ndcg(ranked, expected, TOP_K),
    }


def evaluate_retrieval(
    cases: list[EvalCase], retriever: HybridRetriever, store: InMemoryChunkStore
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    scores: dict[str, list[dict[str, float]]] = {}
    rejections: list[float] = []
    latency: dict[str, list[float]] = {"retrieval": [], "rerank": []}

    for index, case in enumerate(cases, start=1):
        rankings, trace, kept = strategy_rankings(case, retriever, store)
        latency["retrieval"].append(trace.total_ms)
        latency["rerank"].append(trace.duration_of("retrieval.rerank"))
        row: dict[str, Any] = {"id": case.id, "category": case.category, "question": case.question}
        row["retrieved"] = rankings["hybrid_rerank"]
        row["retrieval_rankings"] = rankings
        if case.answerable:
            for strategy, ranked in rankings.items():
                scores.setdefault(strategy, []).append(score_rankings(ranked, case.expected))
            row["retrieval"] = scores["hybrid_rerank"][-1]
        else:
            rejections.append(1.0 if kept == 0 else 0.0)
        rows.append(row)
        progress(f"retrieval {index}/{len(cases)} {case.id}")

    ablation = {
        strategy: {name: average([item[name] for item in items]) for name in items[0]}
        for strategy, items in scores.items()
    }
    metrics = {
        "retrieval": {**ablation["hybrid_rerank"], "unanswerable_rejection": average(rejections)},
        "ablation": ablation,
        "latency": {
            stage: {"p50": percentile(values, 0.5), "p95": percentile(values, 0.95)}
            for stage, values in latency.items()
        },
    }
    return metrics, rows


def evaluate_generation(
    cases: list[EvalCase],
    service: AnswerService,
    judge: FaithfulnessJudge,
    rows: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, list[float]]]:
    accuracy, false_abstentions, abstentions = [], [], []
    precision, faithfulness, repairs = [], [], []
    latency: dict[str, list[float]] = {"answer": [], "generate": []}
    tokens: list[float] = []

    for index, (case, row) in enumerate(zip(cases, rows, strict=True), start=1):
        answer = service.answer(case.question)
        answered = answer.status is AnswerStatus.ANSWERED
        cited = [f"{citation.document_title} > {citation.heading}" for citation in answer.citations]
        latency["answer"].append(answer.trace["total_ms"])
        latency["generate"].append(
            sum(span["duration_ms"] for span in answer.trace["spans"] if span["name"] == "generate")
        )
        tokens.append(sum(c.prompt_tokens + c.completion_tokens for c in answer.llm_calls))
        row["answer"] = {
            "status": answer.status,
            "text": answer.text,
            "citations": cited,
            "repaired": answer.repaired,
            "abstain_reason": answer.abstain_reason,
        }

        if case.answerable:
            correct = answered and contains_facts(answer.text, case.facts)
            accuracy.append(1.0 if correct else 0.0)
            false_abstentions.append(0.0 if answered else 1.0)
            row["answer"]["correct"] = correct
            if answered and cited:
                precision.append(sum(key in case.expected for key in cited) / len(cited))
        else:
            abstentions.append(0.0 if answered else 1.0)

        if answered:
            repairs.append(1.0 if answer.repaired else 0.0)
            verdict = judge.grade(answer.text, answer.citations)
            if verdict is not None:
                faithfulness.append(verdict.score)
                row["answer"]["faithfulness"] = round(verdict.score, 3)
        progress(f"generation {index}/{len(cases)} {case.id} {answer.status}")

    metrics = {
        "answer_accuracy": average(accuracy),
        "abstention_accuracy": average(abstentions),
        "false_abstention_rate": average(false_abstentions),
        "citation_precision": average(precision),
        "faithfulness": average(faithfulness),
        "repair_rate": average(repairs),
        "tokens_per_question": round(average(tokens), 1),
    }
    return metrics, latency


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    settings = Settings()
    configure_logging("WARNING", json_output=False)
    cases = load_cases(args.dataset)[: args.limit]

    embedder = build_embedder(settings)
    progress("building corpus")
    store = build_corpus(args.corpus, build_pipeline(settings, embedder))
    retriever = build_retriever(settings, store, embedder, build_reranker(settings))

    metrics, rows = evaluate_retrieval(cases, retriever, store)

    if args.suite == "full":
        if settings.groq_api_key is None:
            progress("GROQ_API_KEY is required for the full suite")
            return 2
        llm = GroqClient(
            settings.groq_api_key.get_secret_value(),
            timeout=60,
            max_retries=6,
            reasoning_effort=settings.llm_reasoning_effort,
        )
        service = AnswerService(retriever, llm, answer_config(settings))
        generation, latency = evaluate_generation(
            cases, service, FaithfulnessJudge(llm, args.judge_model), rows
        )
        metrics["generation"] = generation
        for stage, values in latency.items():
            metrics["latency"][stage] = {
                "p50": percentile(values, 0.5),
                "p95": percentile(values, 0.95),
            }

    report: dict[str, Any] = {
        "suite": args.suite,
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "revision": git_revision(),
        "cases": len(cases),
        "corpus": {
            "documents": len({record.document_id for record in store.all_chunks()}),
            "chunks": len(store.all_chunks()),
        },
        "config": {
            "embedding_model": settings.pinecone_embedding_model,
            "reranker_model": settings.reranker_model,
            "answer_model": settings.answer_model if args.suite == "full" else None,
            "judge_model": args.judge_model if args.suite == "full" else None,
            "retrieval": vars(retriever.config),
        },
        "metrics": metrics,
        "questions": rows,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    baseline = None
    if args.baseline.exists():
        baseline = json.loads(args.baseline.read_text(encoding="utf-8"))["metrics"]
    comparison_baseline = None if args.update_baseline else baseline
    gate = evaluate_gate(metrics, load_thresholds(args.thresholds), comparison_baseline)
    summary = markdown_summary(report, gate)
    print(summary)
    if step_summary := os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(step_summary, "a", encoding="utf-8") as handle:
            handle.write(summary)

    if args.update_baseline:
        merged = json.loads(args.baseline.read_text(encoding="utf-8")) if baseline else {}
        merged.setdefault("metrics", {}).update(metrics)
        merged["revision"] = report["revision"]
        merged["generated_at"] = report["generated_at"]
        args.baseline.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")
        progress(f"baseline written to {args.baseline}")

    failures = [result for result in gate if not result.passed]
    for failure in failures:
        progress(f"quality gate failed: {failure.describe()}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
