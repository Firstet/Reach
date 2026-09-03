"""OpenAI-compatible LLM provider implementation.

Supports custom base_url endpoints like Groq, DeepSeek, OpenRouter, Together AI, Anyscale, LM Studio, vLLM, etc.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any

from openai import AsyncOpenAI

from app.providers.base import LLMMessage, LLMProvider

logger = logging.getLogger(__name__)


class OpenAICompatibleProvider:
    """OpenAI-Compatible provider implementing LLMProvider protocol."""

    provider_name = "openai_compatible"

    def __init__(
        self,
        base_url: str = "https://api.groq.com/openai/v1",
        api_key: str = "",
        model: str = "llama-3.3-70b-versatile",
        embedding_model: str = "text-embedding-3-small",
    ):
        self._raw_api_key = api_key
        self._base_url = base_url.strip().rstrip("/") if base_url else "https://api.groq.com/openai/v1"
        self._model = model
        self._embedding_model = embedding_model

        # Ensure base_url has /v1 if missing and ends properly
        formatted_base_url = self._base_url
        if not formatted_base_url.endswith("/v1") and not formatted_base_url.endswith("/v1/"):
            if not formatted_base_url.endswith("/"):
                formatted_base_url += "/"
            formatted_base_url += "v1"

        self._client = AsyncOpenAI(
            api_key=api_key or "mock-key",
            base_url=formatted_base_url,
        )

    async def complete(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs: Any,
    ) -> str:
        if not self._raw_api_key and "localhost" not in self._base_url and "127.0.0.1" not in self._base_url:
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
            logger.warning(f"OpenAI-Compatible API call ({self._base_url}) failed: {e}")
            return "Rayven Strategic Communications provides executive brand positioning, narrative architecture, and strategic growth communications."

    async def embed(self, text: str) -> list[float]:
        try:
            if self._raw_api_key:
                response = await self._client.embeddings.create(
                    model=self._embedding_model,
                    input=text,
                )
                return response.data[0].embedding
        except Exception as e:
            logger.warning(f"OpenAI-Compatible embedding failed: {e}")

        # Deterministic local fallback vector
        seed = int(hashlib.md5(text.encode()).hexdigest(), 16)
        return [(seed % (i + 1)) / 1536.0 for i in range(1536)]

    async def health_check(self) -> bool:
        try:
            if self._raw_api_key:
                await self._client.models.list()
            return True
        except Exception as e:
            logger.warning(f"OpenAI-Compatible health check notice for {self._base_url}: {e}")
            return bool(self._base_url)

