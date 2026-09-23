from app.core.config import Settings
from app.db.models import EMBEDDING_DIMENSIONS
from app.db.session import SessionFactory
from app.generation.answerer import AnswerConfig, AnswerService
from app.generation.llm import GroqClient, LLMClient, UnconfiguredClient
from app.ingestion.pipeline import IngestionPipeline
from app.ingestion.worker import IngestionWorker
from app.retrieval.embeddings import Embedder, FastEmbedEmbedder
from app.retrieval.rerank import CrossEncoderReranker, Reranker
from app.retrieval.retriever import HybridRetriever, RetrievalConfig
from app.retrieval.store import ChunkStore


def build_embedder(settings: Settings) -> FastEmbedEmbedder:
    return FastEmbedEmbedder(
        settings.embedding_model, EMBEDDING_DIMENSIONS, settings.model_cache_dir
    )


def build_reranker(settings: Settings) -> CrossEncoderReranker:
    return CrossEncoderReranker(settings.reranker_model, settings.model_cache_dir)


def build_pipeline(settings: Settings, embedder: Embedder) -> IngestionPipeline:
    return IngestionPipeline(embedder, settings.chunk_max_words, settings.chunk_overlap_words)


def build_worker(
    settings: Settings, session_factory: SessionFactory, pipeline: IngestionPipeline
) -> IngestionWorker:
    return IngestionWorker(
        session_factory,
        pipeline,
        max_attempts=settings.worker_max_attempts,
        stale_after_seconds=settings.worker_stale_after_seconds,
        poll_seconds=settings.worker_poll_seconds,
    )


def retrieval_config(settings: Settings) -> RetrievalConfig:
    return RetrievalConfig(
        dense_candidates=settings.retrieval_dense_candidates,
        lexical_candidates=settings.retrieval_lexical_candidates,
        rerank_candidates=settings.retrieval_rerank_candidates,
        top_k=settings.retrieval_top_k,
        min_relevance=settings.retrieval_min_relevance,
        rrf_k=settings.retrieval_rrf_k,
    )


def build_retriever(
    settings: Settings, store: ChunkStore, embedder: Embedder, reranker: Reranker
) -> HybridRetriever:
    return HybridRetriever(store, embedder, reranker, retrieval_config(settings))


def build_llm(settings: Settings) -> LLMClient:
    if settings.groq_api_key is None or not settings.groq_api_key.get_secret_value():
        return UnconfiguredClient()
    return GroqClient(
        settings.groq_api_key.get_secret_value(),
        timeout=settings.llm_timeout_seconds,
        max_retries=settings.llm_max_retries,
    )


def answer_config(settings: Settings) -> AnswerConfig:
    return AnswerConfig(
        answer_model=settings.answer_model,
        rewrite_model=settings.rewrite_model,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
        min_citation_coverage=settings.citation_min_coverage,
        history_messages=settings.chat_history_messages,
    )


def build_answer_service(
    settings: Settings, retriever: HybridRetriever, llm: LLMClient
) -> AnswerService:
    return AnswerService(retriever, llm, answer_config(settings))
