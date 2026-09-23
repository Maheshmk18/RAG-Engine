from functools import lru_cache
from typing import Annotated, Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

DEVELOPMENT_JWT_SECRET = "development-only-secret-never-use-in-production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: Literal["development", "test", "production"] = "development"
    app_name: str = "Ask My Docs"
    api_prefix: str = "/api/v1"
    log_level: str = "INFO"
    log_json: bool = False

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/ragengine"
    database_pool_size: int = 5
    database_max_overflow: int = 10

    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 720

    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173"]
    login_rate_limit: int = 10
    login_rate_window_seconds: int = 300

    @field_validator("database_url")
    @classmethod
    def use_psycopg_driver(cls, value: str) -> str:
        for prefix in ("postgres://", "postgresql://"):
            if value.startswith(prefix):
                return "postgresql+psycopg://" + value.removeprefix(prefix)
        return value

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip().rstrip("/") for origin in value.split(",") if origin.strip()]
        return value

    @model_validator(mode="after")
    def require_secret_in_production(self) -> "Settings":
        if self.environment == "production" and len(self.jwt_secret) < 32:
            raise ValueError("JWT_SECRET must be set to at least 32 characters in production")
        if not self.jwt_secret:
            self.jwt_secret = DEVELOPMENT_JWT_SECRET
        return self

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
