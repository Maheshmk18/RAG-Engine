import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_cors_origins_accept_comma_separated_values() -> None:
    settings = Settings(cors_origins="https://a.example.com/, https://b.example.com")
    assert settings.cors_origins == ["https://a.example.com", "https://b.example.com"]


def test_short_admin_key_is_rejected() -> None:
    with pytest.raises(ValidationError, match="ADMIN_API_KEY"):
        Settings(admin_api_key="short")


def test_blank_keys_count_as_unset() -> None:
    settings = Settings(admin_api_key="  ", groq_api_key="")
    assert settings.admin_api_key is None
    assert settings.groq_api_key is None


def test_vector_search_mode_is_validated() -> None:
    with pytest.raises(ValidationError):
        Settings(vector_search="elastic")
