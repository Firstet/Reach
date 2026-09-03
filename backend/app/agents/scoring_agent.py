"""
Scoring Agent
Executes weighted scoring workflow for a lead.
"""

from __future__ import annotations

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditAction, AuditLog, Lead
from app.services.scoring import ScoringService

logger = logging.getLogger(__name__)


async def run_scoring_agent(
    db: AsyncSession,
    lead_id: uuid.UUID,
    custom_weights: dict | None = None,
) -> dict:
    """Run scoring workflow for a lead."""
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise ValueError(f"Lead {lead_id} not found")

    service = ScoringService(db)

    try:
        score_obj = await service.score_lead(lead_id, custom_weights)
        db.add(AuditLog(
            action=AuditAction.LEAD_SCORED,
            resource_type="lead_score",
            resource_id=str(score_obj.id),
            details={
                "total_score": score_obj.total_score,
                "is_qualified": score_obj.is_qualified,
                "reason": score_obj.qualification_reason,
            },
        ))
        await db.commit()
        return {
            "lead_id": str(lead_id),
            "score": score_obj.total_score,
            "is_qualified": score_obj.is_qualified,
            "tier": score_obj.scoring_metadata.get("tier") if score_obj.scoring_metadata else "UNKNOWN",
        }
    except Exception as e:
        logger.error(f"Scoring agent failed for lead {lead_id}: {e}", exc_info=True)
        return {"lead_id": str(lead_id), "status": "failed", "error": str(e)}
