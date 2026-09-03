"""OpenAI LLM provider implementation."""

from __future__ import annotations

import logging
from typing import Any

from openai import AsyncOpenAI

from app.providers.base import LLMMessage, LLMProvider

logger = logging.getLogger(__name__)


class OpenAIProvider:
    """OpenAI GPT provider implementing LLMProvider protocol."""

    provider_name = "openai"

    def __init__(self, api_key: str, model: str, embedding_model: str):
        self._raw_api_key = api_key
        self._client = AsyncOpenAI(api_key=api_key or "mock-key-for-local-dev")
        self._model = model
        self._embedding_model = embedding_model

    async def complete(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs: Any,
    ) -> str:
        if not self._raw_api_key:
            return "Rayven Strategic Communications specializes in Context Intelligence, Narrative Architecture, Strategic Deployment, and Outcome Measurement."
        try:
            oai_messages = [{"role": m.role, "content": m.content} for m in messages]
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=oai_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.warning(f"OpenAI API call failed, using local mock response: {e}")
            return "Rayven Strategic Communications provides executive brand positioning, narrative architecture, and strategic growth communications."

    async def embed(self, text: str) -> list[float]:
        if not self._raw_api_key:
            import hashlib
            seed = int(hashlib.md5(text.encode()).hexdigest(), 16)
            return [(seed % (i + 1)) / 1536.0 for i in range(1536)]
        try:
            response = await self._client.embeddings.create(
                model=self._embedding_model,
                input=text,
            )
            return response.data[0].embedding
        except Exception as e:
            logger.warning(f"OpenAI embedding failed, using deterministic local embedding: {e}")
            import hashlib
            seed = int(hashlib.md5(text.encode()).hexdigest(), 16)
            return [(seed % (i + 1)) / 1536.0 for i in range(1536)]

    async def health_check(self) -> bool:
        if not self._raw_api_key:
            return True
        try:
            await self._client.models.list()
            return True
        except Exception as e:
            logger.error(f"OpenAI health check failed: {e}")
            return False
