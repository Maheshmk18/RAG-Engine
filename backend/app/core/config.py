import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Enterprise RAG Assistant"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    DATABASE_URL: str = os.environ.get("DATABASE_URL", "")

    SECRET_KEY: str = os.environ.get("SESSION_SECRET", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    OPENAI_API_KEY: Optional[str] = os.environ.get("OPENAI_API_KEY")

    CHROMA_PERSIST_DIRECTORY: str = "./chroma_db"

    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    class Config:
        case_sensitive = True

settings = Settings()