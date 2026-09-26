from app.core.config import Settings


def test_cors_origins_accept_comma_separated_values() -> None:
    settings = Settings(cors_origins="https://a.example.com/, https://b.example.com")
    assert settings.cors_origins == ["https://a.example.com", "https://b.example.com"]


def test_blank_groq_key_counts_as_unset() -> None:
    settings = Settings(groq_api_key="")
    assert settings.groq_api_key is None


def test_pinecone_settings_can_be_configured() -> None:
    settings = Settings(
        pinecone_api_key="test-key",
        pinecone_index_name="test-index",
        pinecone_namespace="test-namespace",
    )
    assert settings.pinecone_index_name == "test-index"
    assert settings.pinecone_namespace == "test-namespace"
