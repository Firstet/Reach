"""
Research Agent
Orchestrates deep research on leads using LLM and web search provider.
"""

from __future__ import annotations

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditAction, AuditLog, Lead
from app.providers.registry import get_llm_provider, get_search_provider
from app.services.research import ResearchService

logger = logging.getLogger(__name__)


async def run_research_agent(db: AsyncSession, lead_id: uuid.UUID) -> dict:
    """Run research workflow for a specific lead."""
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise ValueError(f"Lead {lead_id} not found")

    service = ResearchService(db)
    llm = get_llm_provider()
    search = get_search_provider()

    try:
        research = await service.research_lead(lead_id, llm, search)
        db.add(AuditLog(
            action=AuditAction.AGENT_COMPLETED,
            resource_type="prospect_research",
            resource_id=str(research.id),
            details={"lead_id": str(lead_id), "confidence": research.confidence},
        ))
        await db.commit()
        return {"lead_id": str(lead_id), "status": "researched", "confidence": research.confidence}
    except Exception as e:
        logger.error(f"Research agent failed for lead {lead_id}: {e}", exc_info=True)
        db.add(AuditLog(
            action=AuditAction.AGENT_FAILED,
            resource_type="lead",
            resource_id=str(lead_id),
            details={"error": str(e)},
        ))
        await db.commit()
        return {"lead_id": str(lead_id), "status": "failed", "error": str(e)}
