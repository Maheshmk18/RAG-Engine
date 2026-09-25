from collections.abc import Iterator
from dataclasses import dataclass
from typing import Literal, Protocol, TypedDict, cast

import groq
from groq.types.chat import ChatCompletionMessageParam


class ChatMessage(TypedDict):
    role: Literal["system", "user", "assistant"]
    content: str


@dataclass(frozen=True)
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


@dataclass(frozen=True)
class Completion:
    text: str
    model: str
    usage: Usage


class LLMUnavailableError(Exception):
    def __init__(self, message: str, *, reason: str, detail: str | None = None) -> None:
        super().__init__(message)
        self.reason = reason
        self.detail = detail


class LLMClient(Protocol):
    def complete(
        self, messages: list[ChatMessage], *, model: str, temperature: float, max_tokens: int
    ) -> Completion: ...

    def stream(
        self, messages: list[ChatMessage], *, model: str, temperature: float, max_tokens: int
    ) -> Iterator[str | Completion]: ...


REASONING_MODEL_PREFIX = "openai/gpt-oss"

ReasoningEffort = Literal["low", "medium", "high"]


def provider_messages(messages: list[ChatMessage]) -> list[ChatCompletionMessageParam]:
    return cast(list[ChatCompletionMessageParam], messages)


def translate_error(exc: groq.GroqError) -> LLMUnavailableError:
    detail = str(exc)[:300]
    if isinstance(exc, groq.RateLimitError):
        return LLMUnavailableError(
            "The language model is rate limited", reason="rate_limited", detail=detail
        )
    if isinstance(exc, groq.AuthenticationError | groq.PermissionDeniedError):
        return LLMUnavailableError(
            "The language model rejected the API key", reason="auth", detail=detail
        )
    if isinstance(exc, groq.NotFoundError):
        return LLMUnavailableError(
            "The configured model is not available to this API key",
            reason="model_not_found",
            detail=detail,
        )
    if isinstance(exc, groq.APITimeoutError):
        return LLMUnavailableError("The language model timed out", reason="timeout", detail=detail)
    if isinstance(exc, groq.APIConnectionError):
        return LLMUnavailableError(
            "The language model is unreachable", reason="network", detail=detail
        )
    return LLMUnavailableError(
        "The language model returned an error", reason="provider_error", detail=detail
    )


class GroqClient:
    def __init__(
        self,
        api_key: str,
        timeout: float,
        max_retries: int,
        reasoning_effort: ReasoningEffort | None = None,
    ) -> None:
        self.client = groq.Groq(api_key=api_key, timeout=timeout, max_retries=max_retries)
        self.reasoning_effort = reasoning_effort

    def effort_for(self, model: str) -> ReasoningEffort | groq.Omit:
        if self.reasoning_effort and model.startswith(REASONING_MODEL_PREFIX):
            return self.reasoning_effort
        return groq.omit

    def complete(
        self, messages: list[ChatMessage], *, model: str, temperature: float, max_tokens: int
    ) -> Completion:
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=provider_messages(messages),
                temperature=temperature,
                max_tokens=max_tokens,
                reasoning_effort=self.effort_for(model),
            )
        except groq.GroqError as exc:
            raise translate_error(exc) from exc
        usage = response.usage
        return Completion(
            text=response.choices[0].message.content or "",
            model=response.model,
            usage=Usage(
                usage.prompt_tokens if usage else 0, usage.completion_tokens if usage else 0
            ),
        )

    def stream(
        self, messages: list[ChatMessage], *, model: str, temperature: float, max_tokens: int
    ) -> Iterator[str | Completion]:
        parts: list[str] = []
        usage = Usage()
        served_model = model
        try:
            chunks = self.client.chat.completions.create(
                model=model,
                messages=provider_messages(messages),
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                reasoning_effort=self.effort_for(model),
            )
            for chunk in chunks:
                served_model = chunk.model or served_model
                final_usage = chunk.x_groq.usage if chunk.x_groq else chunk.usage
                if final_usage is not None:
                    usage = Usage(final_usage.prompt_tokens, final_usage.completion_tokens)
                delta = chunk.choices[0].delta.content if chunk.choices else None
                if delta:
                    parts.append(delta)
                    yield delta
        except groq.GroqError as exc:
            raise translate_error(exc) from exc
        yield Completion(text="".join(parts), model=served_model, usage=usage)


class UnconfiguredClient:
    def complete(
        self, messages: list[ChatMessage], *, model: str, temperature: float, max_tokens: int
    ) -> Completion:
        raise LLMUnavailableError("GROQ_API_KEY is not configured", reason="not_configured")

    def stream(
        self, messages: list[ChatMessage], *, model: str, temperature: float, max_tokens: int
    ) -> Iterator[str | Completion]:
        raise LLMUnavailableError("GROQ_API_KEY is not configured", reason="not_configured")
