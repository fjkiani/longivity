"""
OpenRouter-backed LLM bridge for research_intelligence.

Uses the OpenAI-compatible API at https://openrouter.ai/api/v1.
Default model: nvidia/nemotron-3-super-120b-a12b:free

Environment variables:
  OPENROUTER_API_KEY   — required (sk-or-v1-...)
  OPENROUTER_MODEL     — optional override (default: nvidia/nemotron-3-super-120b-a12b:free)
  OPENROUTER_TEMPERATURE — optional override (default: 0.2)

Legacy env vars still accepted for backward compat:
  GROQ_API_KEY         — ignored (OpenRouter key takes precedence)
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from openai import OpenAI


@dataclass
class LLMResponse:
    text: str


class LLMProvider(str, Enum):
    """Legacy enum values — all resolve to OpenRouter here."""

    GROQ = "groq"
    COHERE = "cohere"
    OPENAI = "openai"
    OPENROUTER = "openrouter"


_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
_DEFAULT_MODEL = "nvidia/nemotron-3-super-120b-a12b:free"
_DEFAULT_TEMPERATURE = 0.2


class OpenRouterLLMProvider:
    """OpenRouter provider using the OpenAI-compatible API."""

    def __init__(self) -> None:
        self._model = os.environ.get("OPENROUTER_MODEL", _DEFAULT_MODEL)
        self._temp_default = float(
            os.environ.get("OPENROUTER_TEMPERATURE", str(_DEFAULT_TEMPERATURE))
        )

    def _get_key(self) -> str:
        return os.environ.get("OPENROUTER_API_KEY", "").strip()

    def is_available(self) -> bool:
        return bool(self._get_key())

    async def chat(
        self,
        *,
        message: Optional[str] = None,
        prompt: Optional[str] = None,
        system_message: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        user = message if message is not None else prompt
        if user is None:
            raise ValueError("chat() requires message= or prompt=")

        key = self._get_key()
        if not key:
            raise RuntimeError("OPENROUTER_API_KEY is not set")

        temp = float(temperature if temperature is not None else self._temp_default)

        def _call() -> str:
            client = OpenAI(
                api_key=key,
                base_url=_OPENROUTER_BASE_URL,
            )
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": user})

            r = client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=temp,
                max_tokens=max_tokens,
                extra_headers={
                    "HTTP-Referer": "https://longivity.app",
                    "X-Title": "Longivity Research Intelligence",
                },
            )
            return (r.choices[0].message.content or "").strip()

        text = await asyncio.to_thread(_call)
        return LLMResponse(text=text)


# Backward-compat alias — code that imports GroqLLMProvider still works
GroqLLMProvider = OpenRouterLLMProvider


def get_llm_provider(provider: Optional[LLMProvider] = None) -> OpenRouterLLMProvider:
    """Return the active LLM provider (OpenRouter)."""
    _ = provider  # all enum values resolve to OpenRouter
    return OpenRouterLLMProvider()
