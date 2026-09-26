from functools import lru_cache
from typing import Annotated, Literal

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: Literal["development", "test", "production"] = "development"
    app_name: str = "Enterprise RAG"
    api_prefix: str = "/api/v1"
    log_level: str = "INFO"
    log_json: bool = False

    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_database: str = "enterprise_rag"
    pinecone_api_key: SecretStr | None = None
    pinecone_index_name: str = "enterprise-rag"
    pinecone_namespace: str = "enterprise-rag"
    pinecone_embedding_model: str = "multilingual-e5-large"
    pinecone_embedding_dimensions: int = 1024

    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173"]
    chat_rate_limit_per_minute: int = 20
    upload_rate_limit_per_hour: int = 30

    max_upload_mb: int = 20
    model_cache_dir: str | None = None
    chunk_max_words: int = 180
    chunk_overlap_words: int = 30
    embedded_worker: bool = False
    worker_poll_seconds: float = 2.0
    worker_max_attempts: int = 3
    worker_stale_after_seconds: int = 600

    warm_models_on_startup: bool = True
    reranker_model: str = "Xenova/ms-marco-MiniLM-L-6-v2"
    retrieval_dense_candidates: int = 30
    retrieval_lexical_candidates: int = 30
    retrieval_rerank_candidates: int = 12
    retrieval_top_k: int = 5
    retrieval_min_relevance: float = 0.00005
    retrieval_rrf_k: int = 60

    groq_api_key: SecretStr | None = None
    answer_model: str = "openai/gpt-oss-120b"
    rewrite_model: str = "openai/gpt-oss-20b"
    llm_reasoning_effort: Literal["low", "medium", "high"] | None = "low"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 800
    llm_timeout_seconds: float = 30.0
    llm_max_retries: int = 2
    citation_min_coverage: float = 0.8
    chat_history_messages: int = 6
    chat_max_question_chars: int = 2000

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip().rstrip("/") for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("groq_api_key", "pinecone_api_key", mode="before")
    @classmethod
    def blank_is_unset(cls, value: object) -> object:
        return None if isinstance(value, str) and not value.strip() else value

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
