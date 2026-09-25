import groq
import httpx

from app.generation.llm import GroqClient, translate_error


def status_error(kind: type[groq.APIStatusError], status: int, message: str) -> groq.APIStatusError:
    request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    response = httpx.Response(status, request=request)
    return kind(message, response=response, body=None)


def test_reasoning_effort_only_applies_to_reasoning_models() -> None:
    client = GroqClient("gsk-test", timeout=5, max_retries=0, reasoning_effort="low")
    assert client.effort_for("openai/gpt-oss-120b") == "low"
    assert client.effort_for("qwen/qwen3.8-27b") is groq.omit
    assert GroqClient("gsk-test", timeout=5, max_retries=0).effort_for("openai/gpt-oss-20b") is (
        groq.omit
    )


def test_missing_model_is_reported_clearly() -> None:
    error = translate_error(
        status_error(groq.NotFoundError, 404, "The model `retired-model` does not exist")
    )
    assert error.reason == "model_not_found"
    assert "retired-model" in (error.detail or "")


def test_rate_limits_and_auth_failures_keep_their_reason() -> None:
    assert translate_error(status_error(groq.RateLimitError, 429, "slow down")).reason == (
        "rate_limited"
    )
    assert translate_error(status_error(groq.AuthenticationError, 401, "bad key")).reason == "auth"
