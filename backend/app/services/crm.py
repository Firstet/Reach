"""
Lightweight CRM Pipeline Service
Manages 12 pipeline stages: DISCOVERED, QUALIFIED, CONTACTED, ENGAGED, INTERESTED,
HOT, MEETING, PROPOSAL, WON, LOST, NURTURE, DO_NOT_CONTACT.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import AuditAction, AuditLog, CRMStage, Lead, Prospect, User

logger = logging.getLogger(__name__)

CRM_STAGE_LABELS = [
    {"key": "discovered", "label": "Discovered", "color": "#4c7bc9"},
    {"key": "qualified", "label": "Qualified", "color": "#4caf50"},
    {"key": "contacted", "label": "Contacted", "color": "#9c88ff"},
    {"key": "engaged", "label": "Engaged", "color": "#c9a84c"},
    {"key": "interested", "label": "Interested", "color": "#9c4cc9"},
    {"key": "hot", "label": "🔥 Hot", "color": "#ff4d4d"},
    {"key": "meeting", "label": "Meeting Scheduled", "color": "#4cb89c"},
    {"key": "proposal", "label": "Proposal Sent", "color": "#e0a800"},
    {"key": "won", "label": "🎉 Won / Client", "color": "#2e7d32"},
    {"key": "lost", "label": "Lost", "color": "#5a5a72"},
    {"key": "nurture", "label": "Nurture", "color": "#00838f"},
    {"key": "do_not_contact", "label": "Do Not Contact", "color": "#c94c4c"},
]


class CRMService:
    """Manages CRM pipeline progression and analytics."""

    def __init__(self, session: AsyncSession):
        self._db = session

    async def update_lead_crm_stage(
        self,
        lead_id: uuid.UUID,
        new_stage: CRMStage,
        operator_id: uuid.UUID | None = None,
        notes: str | None = None,
    ) -> Lead:
        """Update CRM stage for a lead."""
        lead = await self._db.get(Lead, lead_id)
        if not lead:
            raise ValueError(f"Lead {lead_id} not found")

        old_stage = lead.crm_stage
        lead.crm_stage = new_stage
        if notes:
            lead.notes = f"{lead.notes or ''}\n[{new_stage.value.upper()}]: {notes}".strip()

        # Terminal state actions
        if new_stage == CRMStage.DO_NOT_CONTACT:
            lead.is_stopped = True
            lead.stopped_reason = "Moved to Do Not Contact stage"
            if lead.prospect and lead.prospect.email:
                from app.services.safety import SafetyService
                safety = SafetyService(self._db)
                await safety.unsubscribe_prospect(str(lead.prospect.id), reason="CRM Do Not Contact")

        self._db.add(AuditLog(
            user_id=operator_id,
            action=AuditAction.LEAD_UPDATED,
            resource_type="lead",
            resource_id=str(lead.id),
            details={"old_stage": old_stage.value, "new_stage": new_stage.value, "notes": notes},
        ))

        await self._db.commit()
        await self._db.refresh(lead)
        return lead

    async def get_crm_pipeline_summary(self) -> dict[str, Any]:
        """Return counts per CRM stage and full lead lists for CRM board."""
        # Stage count aggregation
        stmt = (
            select(Lead.crm_stage, func.count(Lead.id))
            .group_by(Lead.crm_stage)
        )
        res = await self._db.execute(stmt)
        stage_counts = {stage.value: count for stage, count in res.all()}

        # Fetch leads populated with prospect & company
        leads_stmt = (
            select(Lead)
            .options(
                selectinload(Lead.prospect).selectinload(Prospect.company),
                selectinload(Lead.score),
                selectinload(Lead.research),
            )
            .order_by(Lead.updated_at.desc())
            .limit(200)
        )
        leads_res = await self._db.execute(leads_stmt)
        all_leads = leads_res.scalars().all()

        by_stage: dict[str, list[dict]] = {s["key"]: [] for s in CRM_STAGE_LABELS}

        for lead in all_leads:
            stage_key = lead.crm_stage.value if lead.crm_stage else "discovered"
            if stage_key not in by_stage:
                by_stage[stage_key] = []

            by_stage[stage_key].append({
                "id": str(lead.id),
                "prospect_id": str(lead.prospect_id),
                "full_name": lead.prospect.full_name if lead.prospect else "Unknown",
                "title": lead.prospect.title if lead.prospect else "",
                "email": lead.prospect.email if lead.prospect else "",
                "company_name": lead.prospect.company.name if lead.prospect and lead.prospect.company else "",
                "score": lead.score.total_score if lead.score else None,
                "is_stopped": lead.is_stopped,
                "status": lead.status.value,
                "crm_stage": stage_key,
                "why_rayven": lead.research.why_rayven_relevant if lead.research else None,
                "updated_at": lead.updated_at.isoformat(),
            })

        return {
            "stage_labels": CRM_STAGE_LABELS,
            "stage_counts": stage_counts,
            "pipeline": by_stage,
            "total_leads": sum(stage_counts.values()),
        }
