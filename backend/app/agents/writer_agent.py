"""
Writer Agent
Generates personalized email drafts for qualified leads.
Respects campaign approval_mode: creates OutreachApproval if 'manual', or queues for send if 'auto'.
"""

from __future__ import annotations

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    AuditAction,
    AuditLog,
    Campaign,
    Lead,
    LeadStatus,
    Message,
    MessageDirection,
    MessageStatus,
    OutreachApproval,
)
from app.providers.registry import get_llm_provider
from app.services.personalization import PersonalizationService

logger = logging.getLogger(__name__)


async def run_writer_agent(
    db: AsyncSession,
    lead_id: uuid.UUID,
    step_number: int = 1,
) -> dict:
    """Run writer agent workflow to generate outreach draft."""
    lead = await db.get(Lead, lead_id)
    if not lead or not lead.prospect:
        raise ValueError(f"Lead {lead_id} missing prospect")

    campaign = lead.campaign
    if not campaign:
        raise ValueError(f"Lead {lead_id} missing campaign")

    service = PersonalizationService(db)
    llm = get_llm_provider()

    try:
        outreach = await service.generate_outreach_email(lead_id, step_number=step_number, llm=llm)

        # Create Message record (DRAFT status)
        msg = Message(
            id=uuid.uuid4(),
            lead_id=lead.id,
            direction=MessageDirection.OUTBOUND,
            status=MessageStatus.DRAFT,
            subject=outreach.subject,
            body=outreach.body_text,
            from_email=campaign.created_by_id or None,  # will be set at send time
            to_email=lead.prospect.email,
            is_auto_generated=True,
            generation_metadata={"reasoning": outreach.reasoning, "step": step_number},
        )
        db.add(msg)
        await db.flush()

        # Check Approval Mode
        approval_mode = campaign.approval_mode if campaign else "auto"

        if approval_mode == "manual":
            # Create OutreachApproval for operator review
            approval = OutreachApproval(
                id=uuid.uuid4(),
                lead_id=lead.id,
                subject=outreach.subject,
                body=outreach.body_text,
                status="pending",
            )
            db.add(approval)
            lead.status = LeadStatus.OUTREACH_PENDING
            await db.commit()

            db.add(AuditLog(
                action=AuditAction.AGENT_COMPLETED,
                resource_type="outreach_approval",
                resource_id=str(approval.id),
                details={"lead_id": str(lead_id), "mode": "manual", "subject": outreach.subject},
            ))
            await db.commit()
            return {"lead_id": str(lead_id), "status": "approval_queued", "approval_id": str(approval.id)}

        else:
            # Auto mode: Mark lead as ready for outreach send
            lead.status = LeadStatus.OUTREACH_PENDING
            await db.commit()

            db.add(AuditLog(
                action=AuditAction.AGENT_COMPLETED,
                resource_type="message",
                resource_id=str(msg.id),
                details={"lead_id": str(lead_id), "mode": "auto", "subject": outreach.subject},
            ))
            await db.commit()
            return {"lead_id": str(lead_id), "status": "draft_created", "message_id": str(msg.id)}

    except Exception as e:
        logger.error(f"Writer agent failed for lead {lead_id}: {e}", exc_info=True)
        return {"lead_id": str(lead_id), "status": "failed", "error": str(e)}
