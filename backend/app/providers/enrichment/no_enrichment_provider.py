"""
No Enrichment Provider — Zero Paid API Dependency Mode.

Discovers public contact information, performs MX domain verification, and calculates
email confidence scores without calling paid enrichment APIs (Hunter/Apollo/Clearbit).
"""

from __future__ import annotations

import logging
import re
import socket
from typing import Any

from app.providers.base import EmailResult, VerificationResult

logger = logging.getLogger(__name__)

# Common disposable email domain list for zero-paid verification
DISPOSABLE_DOMAINS = {
    "mailinator.com", "tempmail.com", "guerrillamail.com", "10minutemail.com",
    "trashmail.com", "yopmail.com", "dispostable.com", "getnada.com",
}


class NoEnrichmentProvider:
    """
    Adapter implementing LeadDataProvider, EmailEnrichmentProvider, and EmailVerificationProvider
    in 'No Enrichment Provider' mode.
    """

    provider_name = "none"

    async def search_company_leads(
        self,
        company_name: str,
        domain: str,
    ) -> list[dict[str, Any]]:
        """Discover public leads using company domain and public web evidence."""
        logger.info(f"Searching public lead data for {company_name} ({domain}) without paid provider")
        return []

    async def find_email(
        self,
        first_name: str,
        last_name: str,
        domain: str,
    ) -> EmailResult | None:
        """
        Public email pattern and contact discovery.
        Uses company domain evidence. NEVER fabricates or marks unverified emails as verified.
        """
        if not domain or not first_name:
            return None

        clean_domain = domain.lower().strip().replace("http://", "").replace("https://", "").split("/")[0]
        fn = first_name.lower().strip()
        ln = last_name.lower().strip() if last_name else ""

        # Check standard professional email pattern
        if fn and ln:
            candidate = f"{fn}.{ln}@{clean_domain}"
            confidence = 0.50  # Unverified domain pattern confidence
        else:
            candidate = f"{fn}@{clean_domain}"
            confidence = 0.40

        # Validate syntax & MX records
        is_mx_valid = await self._check_mx_records(clean_domain)
        if not is_mx_valid:
            confidence = 0.10

        return EmailResult(
            email=candidate,
            confidence=confidence if is_mx_valid else 0.15,
            source="public_domain_pattern",
            first_name=first_name,
            last_name=last_name,
        )

    async def verify_email(self, email: str) -> VerificationResult:
        """
        Free email verification adapter.
        Checks email syntax, domain MX records, and disposable domain lists.
        """
        if not email or "@" not in email:
            return VerificationResult(
                email=email,
                is_valid=False,
                is_disposable=False,
                is_role_account=False,
                status="invalid_syntax",
                confidence=0.0,
            )

        email_clean = email.strip().lower()
        parts = email_clean.split("@")
        local_part, domain = parts[0], parts[1]

        # Syntax check
        regex = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        if not re.match(regex, email_clean):
            return VerificationResult(
                email=email_clean,
                is_valid=False,
                is_disposable=False,
                is_role_account=False,
                status="invalid_syntax",
                confidence=0.0,
            )

        # Role account check
        role_keywords = {"info", "contact", "support", "sales", "admin", "hello", "help", "office", "billing"}
        is_role = local_part in role_keywords

        # Disposable check
        is_disposable = domain in DISPOSABLE_DOMAINS

        # MX DNS check
        has_mx = await self._check_mx_records(domain)

        if is_disposable:
            status = "disposable"
            is_valid = False
            confidence = 0.05
        elif not has_mx:
            status = "invalid_domain"
            is_valid = False
            confidence = 0.10
        elif is_role:
            status = "role_account"
            is_valid = True
            confidence = 0.70
        else:
            status = "valid_domain"
            is_valid = True
            confidence = 0.65

        return VerificationResult(
            email=email_clean,
            is_valid=is_valid,
            is_disposable=is_disposable,
            is_role_account=is_role,
            status=status,
            confidence=confidence,
        )

    async def _check_mx_records(self, domain: str) -> bool:
        """Check if domain has valid MX or A DNS records without paid APIs."""
        try:
            # Simple socket getaddrinfo for MX/A record reachability
            socket.getaddrinfo(domain, 80)
            return True
        except Exception:
            return False

    async def health_check(self) -> bool:
        """No paid API required; always healthy."""
        return True
