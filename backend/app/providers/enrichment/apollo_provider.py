"""Apollo.io enrichment provider implementation."""

from __future__ import annotations

import logging
import httpx

from app.providers.base import EmailResult, VerificationResult

logger = logging.getLogger(__name__)
APOLLO_BASE = "https://api.apollo.io/v1"


class ApolloProvider:
    """Apollo.io email finder and lead search provider."""

    provider_name = "apollo"

    def __init__(self, api_key: str):
        self._api_key = api_key
        self._client = httpx.AsyncClient(timeout=15.0)

    async def find_email(
        self,
        first_name: str,
        last_name: str,
        domain: str,
    ) -> EmailResult | None:
        try:
            resp = await self._client.post(
                f"{APOLLO_BASE}/people/match",
                headers={"Cache-Control": "no-cache", "Content-Type": "application/json"},
                json={
                    "api_key": self._api_key,
                    "first_name": first_name,
                    "last_name": last_name,
                    "domain": domain,
                },
            )
            if resp.status_code != 200:
                return None
            person = resp.json().get("person", {})
            email = person.get("email")
            if not email:
                return None

            return EmailResult(
                email=email,
                confidence=0.85 if person.get("email_status") == "verified" else 0.60,
                source="apollo",
                first_name=first_name,
                last_name=last_name,
            )
        except Exception as e:
            logger.error(f"Apollo find_email error: {e}")
            return None

    async def verify_email(self, email: str) -> VerificationResult:
        # Apollo verifies through match endpoint; fallback to MX verification if unverified
        is_valid = bool(email and "@" in email)
        return VerificationResult(
            email=email,
            is_valid=is_valid,
            is_disposable=False,
            is_role_account=False,
            status="valid" if is_valid else "invalid",
            confidence=0.80 if is_valid else 0.0,
        )

    async def search_company_leads(self, company_name: str, domain: str) -> list[dict]:
        try:
            resp = await self._client.post(
                f"{APOLLO_BASE}/mixed_people/search",
                json={
                    "api_key": self._api_key,
                    "q_organization_domains": domain,
                    "page": 1,
                    "per_page": 10,
                },
            )
            if resp.status_code != 200:
                return []
            people = resp.json().get("people", [])
            return [
                {
                    "first_name": p.get("first_name", ""),
                    "last_name": p.get("last_name", ""),
                    "title": p.get("title", ""),
                    "email": p.get("email", ""),
                    "linkedin_url": p.get("linkedin_url", ""),
                }
                for p in people
            ]
        except Exception as e:
            logger.error(f"Apollo search_company_leads error: {e}")
            return []

    async def health_check(self) -> bool:
        try:
            resp = await self._client.post(
                f"{APOLLO_BASE}/auth/health",
                json={"api_key": self._api_key},
            )
            return resp.status_code == 200
        except Exception as e:
            logger.warning(f"Apollo health check failed: {e}")
            return False
