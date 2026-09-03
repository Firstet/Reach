"""
Email Enrichment & Verification Service
Finds business email addresses via enrichment providers, verifies deliverables,
records confidence scores, and enforces verification constraints.
"""

from __future__ import annotations

import logging
import re
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Lead, LeadStatus, Prospect
from app.providers.base import EnrichmentProvider

logger = logging.getLogger(__name__)


class EnrichmentService:
    """Enriches prospects with verified professional email addresses."""

    def __init__(self, session: AsyncSession):
        self._db = session

    async def enrich_prospect_email(
        self,
        prospect_id: uuid.UUID,
        enrichment_provider: EnrichmentProvider | None = None,
    ) -> Prospect:
        """Discover and verify email for a prospect."""
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        stmt = select(Prospect).where(Prospect.id == prospect_id).options(selectinload(Prospect.company))
        res = await self._db.execute(stmt)
        prospect = res.scalar_one_or_none()
        if not prospect:
            raise ValueError(f"Prospect {prospect_id} not found")

        company = prospect.company

        # If email already exists, verify it if not verified
        if prospect.email:
            if not prospect.email_verified and enrichment_provider:
                try:
                    ver_result = await enrichment_provider.verify_email(prospect.email)
                    prospect.email_verified = ver_result.is_valid
                    prospect.email_status = ver_result.status
                    prospect.email_confidence = ver_result.confidence
                except Exception as e:
                    logger.warning(f"Verification failed for {prospect.email}: {e}")
            elif not prospect.email_confidence:
                # Default heuristics if no provider available
                prospect.email_confidence = 0.8 if prospect.email_verified else 0.6
                prospect.email_status = "unverified"

            await self._db.commit()
            return prospect

        # No email exists — attempt discovery if domain available
        domain = company.domain if company else None
        if not domain and company and company.website:
            # Extract domain from website URL
            match = re.search(r"https?://(?:www\.)?([^/]+)", company.website)
            if match:
                domain = match.group(1)

        if domain and enrichment_provider:
            try:
                found = await enrichment_provider.find_email(
                    first_name=prospect.first_name,
                    last_name=prospect.last_name,
                    domain=domain,
                )
                if found and found.email:
                    prospect.email = found.email.lower().strip()
                    prospect.email_confidence = found.confidence
                    prospect.email_status = "discovered"

                    # Immediately verify
                    try:
                        ver = await enrichment_provider.verify_email(found.email)
                        prospect.email_verified = ver.is_valid
                        prospect.email_status = ver.status
                        prospect.email_confidence = ver.confidence
                    except Exception:
                        pass
            except Exception as e:
                logger.error(f"Email discovery failed for {prospect.full_name} @ {domain}: {e}")

        # If still no email, fall back to heuristic pattern guess marked as unverified (confidence 0.4)
        if not prospect.email and domain:
            guessed_email = f"{prospect.first_name.lower()}.{prospect.last_name.lower()}@{domain}"
            prospect.email = guessed_email
            prospect.email_confidence = 0.4
            prospect.email_verified = False
            prospect.email_status = "guessed"

        await self._db.commit()
        await self._db.refresh(prospect)
        return prospect

    async def update_lead_enrichment_status(self, lead_id: uuid.UUID) -> Lead:
        """Update lead status after enrichment."""
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        stmt = select(Lead).where(Lead.id == lead_id).options(selectinload(Lead.prospect))
        res = await self._db.execute(stmt)
        lead = res.scalar_one_or_none()
        if not lead:
            raise ValueError(f"Lead {lead_id} not found")

        if lead.prospect and lead.prospect.email:
            if lead.status in (LeadStatus.NEW, LeadStatus.DISCOVERED):
                lead.status = LeadStatus.ENRICHED

        await self._db.commit()
        await self._db.refresh(lead)
        return lead
