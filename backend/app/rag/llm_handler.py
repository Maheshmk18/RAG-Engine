from typing import Any, Iterable
from functools import lru_cache

import google.generativeai as genai
from openai import OpenAI

from ..config import get_settings
from .nodes import LLMProvider

class GeminiClientProvider(LLMProvider):
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash")

    def generate(self, prompt: str, stream: bool = False) -> Any:
        if stream:
            return self.model.generate_content(prompt, stream=True)
        result = self.model.generate_content(prompt)
        return result.text

class OpenAIClientProvider(LLMProvider):
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.model_name = "gpt-4o-mini"

    def generate(self, prompt: str, stream: bool = False) -> Any:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            stream=stream,
        )
        return response

class CompositeLLMProvider(LLMProvider):
    def __init__(self, primary: LLMProvider, fallback: LLMProvider | None):
        self.primary = primary
        self.fallback = fallback

    def generate(self, prompt: str, stream: bool = False) -> Any:
        try:
            return self.primary.generate(prompt, stream=stream)
        except Exception:
            if self.fallback is not None:
                return self.fallback.generate(prompt, stream=stream)
            raise

@lru_cache(maxsize=1)
def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    provider = settings.primary_ai_provider.lower()
    
    gemini_key = settings.gemini_api_key or settings.google_api_key
    openai_key = settings.openai_api_key
    
    primary: LLMProvider | None = None
    fallback: LLMProvider | None = None
    
    if (provider == "gemini" or provider == "google") and gemini_key:
        primary = GeminiClientProvider(gemini_key)
        if openai_key:
            fallback = OpenAIClientProvider(openai_key)
    elif provider == "openai" and openai_key:
        primary = OpenAIClientProvider(openai_key)
        if gemini_key:
            fallback = GeminiClientProvider(gemini_key)
    elif gemini_key:
        primary = GeminiClientProvider(gemini_key)
    elif openai_key:
        primary = OpenAIClientProvider(openai_key)
        
    if primary is None:
        raise RuntimeError(f"No LLM provider configured. Provider: {provider}, Gemini Key: {bool(gemini_key)}, OpenAI Key: {bool(openai_key)}")
    
    return CompositeLLMProvider(primary, fallback)