# Ask My Docs

A question-answering service over an organisation's internal documents. People ask questions in plain language and get short answers where every factual sentence cites the passage it came from. If the documents don't cover a question, the assistant says so instead of guessing.

The retrieval stack combines BM25 keyword search with vector search, merges the two with reciprocal rank fusion, and reranks the result with a cross-encoder. Generated answers are checked for citations before they are shown. A 49-question evaluation set runs in CI and blocks changes that make retrieval worse.

The repository ships with an eleven-document employee handbook for a fictional company, Kestrel Systems, which serves as both the demo knowledge base and the evaluation corpus.

## Contents

- [How it works](#how-it-works)
- [Results](#results)
- [Running it locally](#running-it-locally)
- [Testing and evaluation](#testing-and-evaluation)
- [Deployment](#deployment)
- [Configuration](#configuration)
- [Project layout](#project-layout)
- [Design decisions](#design-decisions)

## How it works

```mermaid
flowchart LR
    subgraph Ingestion
        U[Upload] --> Q[(documents<br/>status: pending)]
        Q --> W[Worker<br/>SKIP LOCKED]
        W --> X[Extract text<br/>PDF, DOCX, MD, TXT]
        X --> C[Heading-aware<br/>chunking]
        C --> E[bge-small<br/>embeddings]
        E --> P[(PostgreSQL<br/>pgvector HNSW)]
    end

    subgraph Answering
        A[Question] --> RW[Rewrite follow-ups<br/>llama-3.1-8b]
        RW --> D[Vector search]
        RW --> B[BM25]
        D --> F[Reciprocal rank fusion]
        B --> F
        F --> R[Cross-encoder rerank<br/>MiniLM]
        R --> G[Answer with numbered sources<br/>llama-3.3-70b on Groq]
        G --> V{Citation check}
        V -- valid --> S[Stream to user]
        V -- invalid --> RP[One repair attempt]
        RP -- still invalid --> N[Decline]
    end

    P -.-> D
    P -.-> B
```

**Ingestion.** Admins upload PDF, Word, Markdown or text files. Each file is validated by its signature, deduplicated by SHA-256 and stored in PostgreSQL, so the API and worker don't need a shared disk. A separate worker process claims pending documents with `SELECT ... FOR UPDATE SKIP LOCKED`, which means several workers can run safely without a queue service. Text is split along the document's own headings, and long sections are cut on sentence boundaries with overlap. Each chunk is embedded together with its document title and section heading, which noticeably helps retrieval for short chunks. Failures retry up to three times. Unreadable files fail immediately with a message the admin can act on.

**Retrieval.** A question runs through two retrievers:

- **Dense:** pgvector cosine search over `bge-small-en-v1.5` embeddings, behind an HNSW index.
- **Lexical:** Okapi BM25 over the same contextual text. The index is kept in memory and rebuilds whenever the corpus version changes.

Their rankings are merged with reciprocal rank fusion. The top twelve candidates are then rescored by the `ms-marco-MiniLM-L-6-v2` cross-encoder, and the best five go to the model. If even the best candidate scores as clearly unrelated, the question is declined without calling the model at all. Every stage is timed.

**Generation and citation enforcement.** The model receives the passages as numbered sources. Its instructions are to cite a source at the end of every factual sentence, to reply with a fixed token when the sources don't answer the question, and to treat source text as reference material rather than instructions. The draft is then checked:

- every `[n]` must refer to a real source
- at least 80% of claim sentences must carry a citation

A draft that fails gets exactly one repair request listing the specific problems. If the repaired version still fails, the assistant declines instead of showing an unsupported answer. The abstention token is held back from the stream, so users never see it. Follow-up questions are first rewritten into standalone ones by a smaller model, so "and for contractors?" retrieves the right passages.

**Chat.** Conversations are stored per user with each answer's citations, token usage, stage timings and optional thumbs up or down feedback. Answers stream to the browser over server-sent events.

## Results

Retrieval quality on the 49-question golden set, using the committed baseline in [`backend/evals/baseline.json`](backend/evals/baseline.json). Of the 49 questions, 41 are answerable, covering direct lookups, paraphrases, cross-document distractors and multi-section questions. The other 8 are questions the handbook cannot answer, including a prompt-injection attempt.

| Strategy | Hit rate @5 | Recall @5 | MRR | nDCG @5 |
| --- | --- | --- | --- | --- |
| Vector search only | 0.976 | 0.963 | 0.951 | 0.947 |
| BM25 only | 0.927 | 0.915 | 0.808 | 0.828 |
| Hybrid (RRF) | 0.976 | 0.963 | 0.902 | 0.912 |
| **Hybrid + rerank** | **1.000** | **0.988** | **0.981** | **0.976** |

Six of the eight unanswerable questions are rejected at retrieval, before any model call. The other two ask about things that sound like real policy ("bereavement leave", "annual bonus"). Those are left for the model to decline, and the answer-quality suite measures whether it does.

On a laptop CPU, retrieval takes about 600 ms at the median and 880 ms at p95, and most of that is the cross-encoder. [docs/evaluation.md](docs/evaluation.md) explains the methodology and how the evaluation caught a miscalibrated reranker threshold during development.

Answer-quality metrics are produced by the full suite, which needs a Groq API key. It covers answer accuracy against expected facts, abstention accuracy, citation precision, and faithfulness graded by a separate judge model. The nightly [Answer quality](.github/workflows/evaluation.yml) workflow publishes that report.

## Running it locally

You need Python 3.11+, Node 20+, and either Docker or a PostgreSQL 16 instance with the `pgvector` extension.

**With Docker Compose**

```bash
docker compose up --build
```

That starts PostgreSQL with pgvector, the API on port 8000, and the ingestion worker. Then create an account and load the handbook:

```bash
docker compose exec -e ADMIN_PASSWORD='choose-a-strong-password-1' api \
  python -m app.cli create-admin --email you@example.com --name "Your Name"
docker compose cp knowledge_base api:/srv/knowledge_base
docker compose exec api python -m app.cli ingest /srv/knowledge_base
```

**Backend without Docker**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
alembic upgrade head
python -m app.cli create-admin --email you@example.com --name "Your Name"
python -m app.cli ingest ../knowledge_base --process
uvicorn app.main:create_app --factory --reload
```

Run `python -m app.worker` in a second terminal to process uploads made through the web app, or set `EMBEDDED_WORKER=true` to run the worker inside the API process.

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

The dev server runs on http://localhost:5173 and proxies `/api` to the backend. Answers need `GROQ_API_KEY` set in `backend/.env`. Without it, retrieval and the search inspector still work, and chat reports that the model is unavailable.

## Testing and evaluation

```bash
cd backend
ruff check . && ruff format --check . && mypy
TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/ragengine_test pytest
python -m evals.run --suite retrieval
GROQ_API_KEY=... python -m evals.run --suite full
```

```bash
cd frontend
npm run format:check && npm run lint && npm run typecheck && npm test && npm run build
```

The integration tests run against a real PostgreSQL database with pgvector. The suite drops and recreates the schema through the Alembic migrations, so point `TEST_DATABASE_URL` at a throwaway database.

The evaluation gate in [`backend/evals/thresholds.toml`](backend/evals/thresholds.toml) fails the run when any metric drops below its floor, or falls more than 0.02 below the committed baseline. Use `--update-baseline` to record a new baseline after an intentional improvement.

**Continuous integration** runs on every push and pull request:

| Job | What it checks |
| --- | --- |
| Backend checks | Ruff, formatting, mypy, 100 tests against pgvector, `alembic check` for migration drift |
| Retrieval quality gate | The retrieval suite against floors and the baseline |
| Frontend checks | Prettier, ESLint with zero warnings, TypeScript, Vitest, production build |
| Container image | The backend Docker image builds |

The full answer-quality evaluation runs nightly, on demand, and on pushes to `main`, once a `GROQ_API_KEY` repository secret is added.

## Deployment

The backend runs on Railway as two services built from the same image, and the frontend runs on Vercel.

**Railway**

1. Add PostgreSQL from Railway's **pgvector** template. The migrations enable the extension.
2. Create an **api** service from this repository with root directory `backend`. It picks up [`railway.toml`](backend/railway.toml), runs migrations on start and exposes `/api/v1/health/ready` as its health check.
3. Create a **worker** service from the same repository and root directory, and set its config file path to `backend/railway.worker.toml`.
4. Set these variables on both services:

   | Variable | Value |
   | --- | --- |
   | `ENVIRONMENT` | `production` |
   | `DATABASE_URL` | reference the Postgres service's URL |
   | `JWT_SECRET` | at least 32 random characters |
   | `GROQ_API_KEY` | your key |
   | `CORS_ORIGINS` | your Vercel domain, for example `https://ask-my-docs.vercel.app` |
   | `LOG_JSON` | `true` |

5. Create the first administrator from a Railway shell with `python -m app.cli create-admin`.

To run on a single service, skip the worker and set `EMBEDDED_WORKER=true` on the API.

**Vercel**

Import the repository with **root directory `frontend`** and set `VITE_API_URL` to the Railway API's public URL. [`frontend/vercel.json`](frontend/vercel.json) handles SPA routing, asset caching and security headers.

## Configuration

All backend settings are environment variables, documented with defaults in [`backend/.env.example`](backend/.env.example). The ones you are most likely to change:

| Variable | Default | Purpose |
| --- | --- | --- |
| `ANSWER_MODEL` | `llama-3.3-70b-versatile` | Groq model that writes answers |
| `REWRITE_MODEL` | `llama-3.1-8b-instant` | Groq model that rewrites follow-up questions |
| `RETRIEVAL_TOP_K` | `5` | Passages sent to the model |
| `RETRIEVAL_RERANK_CANDIDATES` | `12` | Fused candidates rescored by the cross-encoder |
| `RETRIEVAL_MIN_RELEVANCE` | `0.00005` | Below this best score a question is treated as off-topic |
| `CITATION_MIN_COVERAGE` | `0.8` | Share of claim sentences that must carry a citation |
| `CHUNK_MAX_WORDS` / `CHUNK_OVERLAP_WORDS` | `180` / `30` | Chunk size and overlap |
| `CHAT_RATE_LIMIT_PER_MINUTE` | `20` | Questions per user per minute |

## Project layout

```
backend/
  app/
    api/            HTTP routes, dependencies and request schemas
    core/           settings, logging, errors, security, middleware
    db/             SQLAlchemy models and session handling
    ingestion/      text extraction, chunking, pipeline and worker
    retrieval/      embeddings, BM25, fusion, reranking, hybrid retriever
    generation/     Groq client, prompts, citation checks, answer service
    services/       users, documents, chat and corpus bookkeeping
    telemetry/      per-request stage timing
  evals/            golden dataset, metrics, judge, runner, thresholds, baseline
  migrations/       Alembic migrations
  tests/            unit and PostgreSQL integration tests
frontend/
  src/
    app/            routing, shell and guards
    components/ui/  buttons, fields, dialogs, tables and other primitives
    features/       chat, documents, admin and account screens
    lib/            API client, SSE reader, auth, formatting, citation rendering
knowledge_base/     the demo handbook and evaluation corpus
```

## Design decisions

**One database.** Documents, uploaded files, chunks, vectors, users and chats all live in PostgreSQL. That removes a separate vector database and a shared file store, and a deployment is two stateless services plus Postgres.

**BM25 in the API process.** PostgreSQL full-text ranking isn't BM25, and a search engine would add another service. The index for a document collection of this size builds in milliseconds and is rebuilt only when the corpus version changes. At a few hundred thousand chunks, the lexical side should move to a dedicated search index.

**Local embedding and reranking models.** Groq serves chat models but not embeddings, and the retrieval models are small enough to run on CPU. Both are baked into the container image so cold starts don't download anything. Their cost shows up as latency, which is why every stage is traced.

**The relevance threshold filters only off-topic questions.** Cross-encoder scores aren't calibrated for conversational questions: correct passages sometimes score 0.0001. So the threshold only removes questions nothing in the corpus relates to. Deciding whether an on-topic question is actually answered is left to the grounded prompt and the citation check. [docs/evaluation.md](docs/evaluation.md) has the numbers behind this.

**Withholding beats hedging.** When citations fail validation twice, the user gets an explicit "not covered" answer rather than an unverified one. For internal policy questions, a confident wrong answer is the expensive failure.

**Groundwork for monitoring.** Every answer already records per-stage durations, token counts for each model call, citation coverage, repair and abstention outcomes, and user feedback. Request IDs flow through logs and error responses. Tracing export, latency percentiles, cost per request and regression dashboards can build on this data without changing the pipeline.
