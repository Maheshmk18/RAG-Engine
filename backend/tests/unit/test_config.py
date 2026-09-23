import pytest
from pydantic import ValidationError

from app.core.config import DEVELOPMENT_JWT_SECRET, Settings


def test_database_url_uses_psycopg_driver() -> None:
    settings = Settings(database_url="postgres://user:pass@host:5432/db")
    assert settings.database_url == "postgresql+psycopg://user:pass@host:5432/db"


def test_cors_origins_accept_comma_separated_values() -> None:
    settings = Settings(cors_origins="https://a.example.com/, https://b.example.com")
    assert settings.cors_origins == ["https://a.example.com", "https://b.example.com"]


def test_production_requires_strong_secret() -> None:
    with pytest.raises(ValidationError, match="JWT_SECRET"):
        Settings(environment="production", jwt_secret="too-short")


def test_development_falls_back_to_local_secret() -> None:
    assert Settings(environment="development", jwt_secret="").jwt_secret == DEVELOPMENT_JWT_SECRET
