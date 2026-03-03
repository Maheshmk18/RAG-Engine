from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    project_name: str = "Enterprise RAG Assistant"
    api_prefix: str = "/api/v1"
    database_url: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    primary_ai_provider: str = "gemini"
    gemini_api_key: str | None = None
    openai_api_key: str | None = None
    huggingface_api_key: str | None = None
    hf_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    vector_store_provider: str = "pinecone"
    pinecone_api_key: str | None = None
    pinecone_index_name: str = "enterprise-rag"
    pinecone_region: str = "us-east-1"
    chunk_size: int = 512
    chunk_overlap: int = 50
    top_k: int = 5
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
