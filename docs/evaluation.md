# Evaluation

This page describes how retrieval and answer quality are measured, how to run the suites, and what the evaluation has changed in the retriever.

## Dataset

[`backend/evals/dataset.jsonl`](../backend/evals/dataset.jsonl) contains 49 questions about the Kestrel Systems handbook in [`knowledge_base/`](../knowledge_base). Each row lists the expected handbook sections and, for answerable questions, short facts a correct answer must include.

| Category | Questions | Example |
| --- | ---: | --- |
| Lookup | 14 | How long is the probation period? |
| Paraphrase | 18 | Is there any money for setting up a desk and chair at home? |
| Reasoning | 3 | How far in advance do I need to request a week and a half off? |
| Distractor | 3 | I got ill while I was on vacation. Can I get those days back? |
| Multi-section | 3 | Do I need to use the VPN when working from a cafe? |
| Unanswerable | 8 | How many days of bereavement leave do I get? |

The policies intentionally overlap on notice periods, approvals and leave. The distractor questions check whether retrieval finds the policy that answers the question instead of another policy with similar wording. Metrics use `Document title > Heading` section keys, so they do not depend on how a section is split into chunks.

## Retrieval suite

For each answerable question, the runner compares four rankings using the top five sections:

- **Hit rate @5:** share of questions with at least one expected section in the top five.
- **Recall @5:** share of expected sections found in the top five.
- **MRR:** reciprocal rank of the first expected section.
- **nDCG @5:** rank-weighted score with binary relevance, counting a section once.

For unanswerable questions, it records how often retrieval returns no passages, allowing the app to decline before calling a model. The corpus is built in memory by the production extraction, chunking and embedding pipeline. This suite needs neither MongoDB nor an API key, so CI can run it on pull requests.

## Full answer suite

The full suite runs the same questions through the answer service with the configured Groq models, and grades answered claims with a separate `qwen/qwen3.8-27b` judge by default:

- **Answer accuracy:** an answer was returned and every expected fact appears in it. Matching ignores case, spacing and thousands separators.
- **Abstention accuracy:** unanswerable questions that did not receive an answer.
- **False abstention rate:** answerable questions that did not receive an answer.
- **Citation precision:** the share of cited sections that are expected for the question.
- **Faithfulness:** the judge checks whether each factual claim is supported by the cited passages.
- **Repair rate:** share of answered questions that needed a citation repair call.
- **Tokens per question:** prompt and completion tokens from the answer service's model calls.

The judge model can be changed with `--judge-model`. The full suite requires `GROQ_API_KEY`; it calls the configured answer model and the judge model for each answered question, so it uses more API quota than the retrieval suite.

## Quality gate

[`backend/evals/thresholds.toml`](../backend/evals/thresholds.toml) sets minimum values for the gated metrics. A run fails when a metric falls below its floor or more than `0.02` below the corresponding value in [`backend/evals/baseline.json`](../backend/evals/baseline.json). Floors catch major failures; the baseline comparison catches smaller regressions.

## Current retrieval results

The committed baseline reports these retrieval scores across the 41 answerable questions:

| Strategy | Hit rate @5 | Recall @5 | MRR | nDCG @5 |
| --- | ---: | ---: | ---: | ---: |
| Vector search only | 0.976 | 0.963 | 0.951 | 0.947 |
| BM25 only | 0.927 | 0.915 | 0.808 | 0.828 |
| Hybrid (RRF) | 0.976 | 0.963 | 0.902 | 0.912 |
| **Hybrid + rerank** | **1.000** | **0.988** | **0.981** | **0.976** |

The hybrid reranker rejects six of the eight unanswerable questions before generation. The other two questions sound like real policy topics but are not covered by the handbook, so the answer service must decline them using its grounded prompt and citation checks.

During development, a reranker threshold of `0.1` discarded relevant passages whose conversational queries scored as low as `0.0001`, dropping hit rate to `0.829`. Setting the threshold to `0.00005` and applying it only to the best candidate restored retrieval quality while still rejecting clearly off-topic queries. Retrieval alone cannot distinguish an uncovered in-domain question such as bereavement leave from a covered leave policy; the answer service handles that distinction.

## Run the evaluations

From `backend/`:

```bash
python -m evals.run --suite retrieval
GROQ_API_KEY=... python -m evals.run --suite full
python -m evals.run --suite retrieval --update-baseline
```

Reports default to `backend/evals/reports/latest.json` and include per-question retrieval and answer details. The CI workflows add a Markdown summary to the job and upload their reports as artifacts. Update the committed baseline only when the change is intentional and its quality has been reviewed.
