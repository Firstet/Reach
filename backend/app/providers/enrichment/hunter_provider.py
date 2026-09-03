"""Hunter.io email enrichment provider."""

from __future__ import annotations

import logging

import httpx

from app.providers.base import EmailResult, EnrichmentProvider, VerificationResult

logger = logging.getLogger(__name__)
HUNTER_BASE = "https://api.hunter.io/v2"


class HunterProvider:
    """Hunter.io email finder and verifier."""

    provider_name = "hunter"

    def __init__(self, api_key: str):
        self._api_key = api_key
        self._client = httpx.AsyncClient(timeout=15.0)

    async def find_email(
        self,
        first_name: str,
        last_name: str,
        domain: str,
    ) -> EmailResult | None:
        resp = await self._client.get(
            f"{HUNTER_BASE}/email-finder",
            params={
                "first_name": first_name,
                "last_name": last_name,
                "domain": domain,
                "api_key": self._api_key,
            },
        )
        if resp.status_code != 200:
            return None
        data = resp.json().get("data", {})
        if not data.get("email"):
            return None
        return EmailResult(
            email=data["email"],
            confidence=data.get("score", 0) / 100,
            source="hunter",
            first_name=first_name,
            last_name=last_name,
        )

    async def verify_email(self, email: str) -> VerificationResult:
        resp = await self._client.get(
            f"{HUNTER_BASE}/email-verifier",
            params={"email": email, "api_key": self._api_key},
        )
        data = resp.json().get("data", {})
        return VerificationResult(
            email=email,
            is_valid=data.get("result") == "deliverable",
            is_disposable=data.get("disposable", False),
            is_role_account=data.get("role", False),
            status=data.get("result", "unknown"),
            confidence=data.get("score", 0) / 100,
        )

    async def health_check(self) -> bool:
        try:
            resp = await self._client.get(
                f"{HUNTER_BASE}/account",
                params={"api_key": self._api_key},
            )
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"Hunter health check failed: {e}")
            return False
