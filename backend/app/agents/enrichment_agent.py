"""
Enrichment Agent
Orchestrates email discovery and verification for leads.
"""

from __future__ import annotations

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditAction, AuditLog, Lead
from app.providers.registry import get_enrichment_provider
from app.services.enrichment import EnrichmentService

logger = logging.getLogger(__name__)


async def run_enrichment_agent(db: AsyncSession, lead_id: uuid.UUID) -> dict:
    """Run email enrichment workflow for a lead."""
    lead = await db.get(Lead, lead_id)
    if not lead or not lead.prospect:
        raise ValueError(f"Lead {lead_id} or prospect not found")

    service = EnrichmentService(db)
    provider = get_enrichment_provider()

    try:
        prospect = await service.enrich_prospect_email(lead.prospect.id, provider)
        await service.update_lead_enrichment_status(lead.id)

        db.add(AuditLog(
            action=AuditAction.LEAD_ENRICHED,
            resource_type="prospect",
            resource_id=str(prospect.id),
            details={
                "email": prospect.email,
                "verified": prospect.email_verified,
                "confidence": prospect.email_confidence,
            },
        ))
        await db.commit()
        return {
            "lead_id": str(lead_id),
            "email": prospect.email,
            "verified": prospect.email_verified,
            "confidence": prospect.email_confidence,
        }
    except Exception as e:
        logger.error(f"Enrichment agent failed for lead {lead_id}: {e}", exc_info=True)
        return {"lead_id": str(lead_id), "status": "failed", "error": str(e)}
