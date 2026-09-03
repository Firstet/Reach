"""Anthropic Claude LLM provider implementation."""

from __future__ import annotations

import logging
from typing import Any

import anthropic

from app.providers.base import LLMMessage, LLMProvider

logger = logging.getLogger(__name__)


class AnthropicProvider:
    """Anthropic Claude provider implementing LLMProvider protocol."""

    provider_name = "anthropic"

    def __init__(self, api_key: str, model: str):
        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._model = model

    async def complete(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs: Any,
    ) -> str:
        # Separate system message from conversation
        system = ""
        conversation = []
        for m in messages:
            if m.role == "system":
                system = m.content
            else:
                conversation.append({"role": m.role, "content": m.content})

        response = await self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            system=system,
            messages=conversation,
            temperature=temperature,
        )
        return response.content[0].text

    async def embed(self, text: str) -> list[float]:
        # Anthropic does not offer an embedding API — use OpenAI embeddings
        # or fall back to a local model. Raise to make this explicit.
        raise NotImplementedError(
            "Anthropic does not provide an embedding API. "
            "Configure an embedding-capable provider (e.g. OpenAI) alongside Claude."
        )

    async def health_check(self) -> bool:
        try:
            await self._client.messages.create(
                model=self._model,
                max_tokens=1,
                messages=[{"role": "user", "content": "ping"}],
            )
            return True
        except Exception as e:
            logger.error(f"Anthropic health check failed: {e}")
            return False
