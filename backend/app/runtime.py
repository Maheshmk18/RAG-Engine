from app.core.config import Settings
from app.db.models import EMBEDDING_DIMENSIONS
from app.db.session import SessionFactory
from app.ingestion.pipeline import IngestionPipeline
from app.ingestion.worker import IngestionWorker
from app.retrieval.embeddings import Embedder, FastEmbedEmbedder


def build_embedder(settings: Settings) -> FastEmbedEmbedder:
    return FastEmbedEmbedder(
        settings.embedding_model, EMBEDDING_DIMENSIONS, settings.model_cache_dir
    )


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
