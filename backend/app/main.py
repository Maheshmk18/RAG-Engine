import logging
import threading
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import Settings, get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware
from app.core.rate_limit import SlidingWindowRateLimiter
from app.db.mongo import create_client, ensure_indexes
from app.retrieval.store import MongoChunkStore
from app.runtime import (
    build_answer_service,
    build_embedder,
    build_llm,
    build_pipeline,
    build_reranker,
    build_retriever,
    build_worker,
    warm_up,
)

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level, settings.log_json)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        logger.info("service starting", extra={"environment": settings.environment})
        ensure_indexes(app.state.database, settings)
        stop = threading.Event()
        worker_thread: threading.Thread | None = None
        if settings.warm_models_on_startup:
            threading.Thread(target=warm_up, args=(app.state.retriever,), daemon=True).start()
        if settings.embedded_worker:
            worker = build_worker(settings, app.state.database, app.state.pipeline)
            worker_thread = threading.Thread(target=worker.run, args=(stop,), daemon=True)
            worker_thread.start()
        yield
        stop.set()
        if worker_thread is not None:
            worker_thread.join(timeout=30)
        app.state.mongo.close()
        logger.info("service stopped")

    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        openapi_url=f"{settings.api_prefix}/openapi.json",
        docs_url=f"{settings.api_prefix}/docs",
        redoc_url=None,
        lifespan=lifespan,
    )

    client = create_client(settings)
    app.state.settings = settings
    app.state.mongo = client
    app.state.database = client[settings.mongodb_database]
    app.state.embedder = build_embedder(settings)
    app.state.pipeline = build_pipeline(settings, app.state.embedder)
    app.state.retriever = build_retriever(
        settings,
        MongoChunkStore(app.state.database, settings.vector_search, settings.atlas_vector_index),
        app.state.embedder,
        build_reranker(settings),
    )
    app.state.answer_service = build_answer_service(
        settings, app.state.retriever, build_llm(settings)
    )
    app.state.chat_limiter = SlidingWindowRateLimiter(settings.chat_rate_limit_per_minute, 60)
    app.state.upload_limiter = SlidingWindowRateLimiter(settings.upload_rate_limit_per_hour, 3600)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Content-Type", "X-Request-ID", "X-Client-Id", "X-Admin-Key"],
        expose_headers=["X-Request-ID"],
    )
    app.add_middleware(RequestContextMiddleware)
    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_prefix)
    return app
