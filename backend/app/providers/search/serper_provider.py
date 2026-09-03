"""Serper.dev web search provider."""

from __future__ import annotations

import logging

import httpx

from app.providers.base import SearchProvider, SearchResult

logger = logging.getLogger(__name__)
SERPER_BASE = "https://google.serper.dev/search"


class SerperProvider:
    """Serper.dev Google search provider."""

    provider_name = "serper"

    def __init__(self, api_key: str):
        self._api_key = api_key
        self._client = httpx.AsyncClient(
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            timeout=15.0,
        )

    async def search(
        self,
        query: str,
        num_results: int = 10,
        **kwargs,
    ) -> list[SearchResult]:
        resp = await self._client.post(
            SERPER_BASE,
            json={"q": query, "num": num_results},
        )
        if resp.status_code != 200:
            logger.error(f"Serper API error: {resp.status_code}")
            return []
        results = []
        for item in resp.json().get("organic", []):
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                    source="serper",
                )
            )
        return results

    async def health_check(self) -> bool:
        return bool(self._api_key)

