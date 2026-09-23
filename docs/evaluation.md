# Evaluation

This page describes how answer and retrieval quality are measured, what the current numbers are, and one change the evaluation drove during development.

## The dataset

[`backend/evals/dataset.jsonl`](../backend/evals/dataset.jsonl) holds 49 questions about the Kestrel Systems handbook in [`knowledge_base/`](../knowledge_base). Each record lists the question, the handbook sections that answer it, and short facts a correct answer must contain.

| Category | Count | Example |
| --- | --- | --- |
| Lookup | 14 | How long is the probation period? |
| Paraphrase | 18 | Is there any money for setting up a desk and chair at home? |
| Reasoning | 3 | How far in advance do I need to request a week and a half off? |
| Distractor | 3 | I got ill while I was on vacation. Can I get those days back? |
| Multi-section | 3 | Do I need to use the VPN when working from a cafe? |
| Unanswerable | 8 | How many days of bereavement leave do I get? |

The documents were written to overlap on purpose. Several policies talk about notice periods, approvals, carrying things over and days of leave, so a retriever that matches on shared vocabulary alone gets distracted. The distractor questions target those overlaps. The sick-on-holiday question, for example, sounds like the sick leave policy but is answered by the annual leave policy.

Sections are identified as `Document title > Heading`, so the metrics don't depend on how a section happens to be chunked.

## Retrieval metrics

For each answerable question, the runner records the top five sections from four strategies and scores them:

- **Hit rate @5:** whether any expected section appears in the top five.
- **Recall @5:** the share of expected sections that appear.
- **MRR:** the reciprocal rank of the first expected section.
- **nDCG @5:** rank-weighted gain with binary relevance, counting each section once.

For unanswerable questions, it records whether retrieval returned nothing, which means the model is never called.

The corpus is built in memory with the same extraction, chunking and embedding code as production, so the retrieval suite needs neither a database nor an API key. That's what lets it run on every pull request.

## Answer metrics

The full suite sends every question through the complete answer service using the real Groq models:

- **Answer accuracy:** answered, and every expected fact appears in the answer. Matching ignores case, spacing and thousands separators.
- **Abstention accuracy:** unanswerable questions that were declined.
- **False abstention rate:** answerable questions that were declined.
- **Citation precision:** the share of cited sections that are among the expected ones.
- **Faithfulness:** a separate judge model, `openai/gpt-oss-120b`, splits each answer into claims and marks whether the cited passages support each one. The judge comes from a different model family than the answer model to limit self-preference.
- **Repair rate** and **tokens per question**, to spot regressions in prompt adherence and cost.

## The gate

[`backend/evals/thresholds.toml`](../backend/evals/thresholds.toml) sets a floor for each gated metric. The run fails if a metric falls below its floor, or drops more than 0.02 below the committed [baseline](../backend/evals/baseline.json). The floors catch serious breakage. The baseline comparison catches gradual erosion that would otherwise slip under a generous floor.

## Current retrieval results

| Strategy | Hit rate @5 | Recall @5 | MRR | nDCG @5 |
| --- | --- | --- | --- | --- |
| Vector search only | 0.976 | 0.963 | 0.951 | 0.947 |
| BM25 only | 0.927 | 0.915 | 0.808 | 0.828 |
| Hybrid (RRF) | 0.976 | 0.963 | 0.902 | 0.912 |
| Hybrid + rerank | 1.000 | 0.988 | 0.981 | 0.976 |

Retrieval rejects 6 of the 8 unanswerable questions.

A few observations:

- **Fusion alone does not beat dense search here.** It adds BM25's misses into the candidate list. What fusion buys is recall across both candidate sets, which the reranker then orders. With the reranker on top, the pipeline beats every single strategy on every metric.
- **BM25 helps with exact terms.** For questions containing specific codes and names, such as "SEV1" or "USB", BM25 put the right section first. Paraphrased questions are where it falls behind vector search.
- **Reranker choice.** The MiniLM-L-6 cross-encoder was compared with four alternatives available through fastembed, with no relevance threshold applied:

  | Model | MRR | Median latency for 12 passages |
  | --- | --- | --- |
  | ms-marco-MiniLM-L-6 | 0.980 | 210 ms |
  | ms-marco-MiniLM-L-12 | 0.982 | 372 ms |
  | jina-reranker-v1-tiny-en | 0.915 | 175 ms |
  | jina-reranker-v1-turbo-en | 0.935 | 256 ms |
  | bge-reranker-base | 0.953 | 1568 ms |

  MiniLM-L-12 ranks marginally better but takes almost twice as long. `bge-reranker-base` is about 13 times larger and 7 times slower, and ranks worse on this dataset. MiniLM-L-6 is the default, and `RERANKER_MODEL` switches between them.

## What the first run found

The first version of the retriever dropped any passage whose cross-encoder score was below 0.1. The first evaluation run scored a hit rate of 0.829, worse than either retriever on its own.

The per-question report showed why. In six of the seven failures the cross-encoder had ranked the correct section first, with an absolute score between 0.0001 and 0.045. Its scores are calibrated on web search queries and run very low for conversational phrasing such as "Will the company pay for wine with dinner?", so the threshold was throwing away correct answers.

Sorting the best score for every question made the split clear:

| Best score | Questions |
| --- | --- |
| ≤ 0.00004 | six clearly off-topic questions: dental provider, parking, dog, stock ticker, geography, prompt injection |
| 0.00012 and above | every answerable question, plus two in-domain questions the handbook does not cover |

The threshold was reset to 0.00005, and it now applies to the best candidate only, not to each passage. It filters out questions nothing in the corpus relates to. Deciding whether an on-topic question is actually answered moved to the grounded prompt and the citation check. That's the only layer that can tell "bereavement leave" (not covered) from "carry-over of leave" (covered), since both look like leave policy to a retriever.

## Running it

```bash
cd backend
python -m evals.run --suite retrieval
GROQ_API_KEY=... python -m evals.run --suite full
python -m evals.run --suite retrieval --update-baseline
```

Reports are written to `backend/evals/reports/latest.json` with per-question detail. In GitHub Actions, the summary table is added to the job summary and the report is uploaded as an artifact.
