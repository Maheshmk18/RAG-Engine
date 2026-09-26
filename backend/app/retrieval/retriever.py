from dataclasses import dataclass

from app.retrieval.embeddings import Embedder
from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.lexical import LexicalIndex
from app.retrieval.rerank import Reranker
from app.retrieval.store import ChunkRecord, ChunkStore
from app.telemetry.tracing import Trace


@dataclass(frozen=True)
class RetrievalConfig:
    dense_candidates: int = 30
    lexical_candidates: int = 30
    rerank_candidates: int = 12
    top_k: int = 5
    min_relevance: float = 0.00005
    rrf_k: int = 60


@dataclass(frozen=True)
class Passage:
    chunk: ChunkRecord
    relevance: float
    fused_score: float
    dense_rank: int | None
    lexical_rank: int | None


@dataclass(frozen=True)
class RetrievalResult:
    query: str
    passages: list[Passage]
    candidates: int

    @property
    def best_relevance(self) -> float:
        return max((passage.relevance for passage in self.passages), default=0.0)


def rank_of(ranking: list[str]) -> dict[str, int]:
    return {chunk_id: position for position, chunk_id in enumerate(ranking, start=1)}


class HybridRetriever:
    def __init__(
        self,
        store: ChunkStore,
        embedder: Embedder,
        reranker: Reranker,
        config: RetrievalConfig,
    ) -> None:
        self.store = store
        self.embedder = embedder
        self.reranker = reranker
        self.config = config
        self.lexical = LexicalIndex(store)

    def retrieve(self, query: str, trace: Trace | None = None) -> RetrievalResult:
        trace = trace or Trace()
        config = self.config

        with trace.span("retrieval.dense") as span:
            dense = self.store.vector_search(
                self.embedder.embed_query(query), config.dense_candidates
            )
            span["results"] = len(dense)
        with trace.span("retrieval.lexical") as span:
            lexical = self.lexical.search(query, config.lexical_candidates)
            span["results"] = len(lexical)
        with trace.span("retrieval.fusion") as span:
            fused = reciprocal_rank_fusion([dense, lexical], k=config.rrf_k)
            fused_scores = dict(fused)
            candidate_ids = [chunk_id for chunk_id, _ in fused[: config.rerank_candidates]]
            records = self.store.get_many(candidate_ids)
            candidate_ids = [chunk_id for chunk_id in candidate_ids if chunk_id in records]
            span["candidates"] = len(candidate_ids)

        with trace.span("retrieval.rerank") as span:
            texts = [records[chunk_id].contextual_text for chunk_id in candidate_ids]
            relevance = self.reranker.score(query, texts)
            dense_ranks, lexical_ranks = rank_of(dense), rank_of(lexical)
            reranked = sorted(
                zip(candidate_ids, relevance, strict=True),
                key=lambda item: item[1],
                reverse=True,
            )
            scored = [
                Passage(
                    chunk=records[chunk_id],
                    relevance=score,
                    fused_score=round(fused_scores[chunk_id], 6),
                    dense_rank=dense_ranks.get(chunk_id),
                    lexical_rank=lexical_ranks.get(chunk_id),
                )
                for chunk_id, score in reranked
            ]
            best = max(relevance, default=0.0)
            on_topic = best >= config.min_relevance
            passages = scored[: config.top_k] if on_topic else []
            span["kept"] = len(passages)
            span["best_relevance"] = best

        return RetrievalResult(query=query, passages=passages, candidates=len(candidate_ids))
