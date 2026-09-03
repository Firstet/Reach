"""Outreach approvals & send management router."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.routers.auth import get_current_user
from app.core.database import get_db
from app.models import AuditAction, AuditLog, Lead, LeadStatus, OutreachApproval, User

router = APIRouter(prefix="/outreach", tags=["outreach"])


class ApprovalActionRequest(BaseModel):
    subject: str | None = None
    body: str | None = None
    rejection_reason: str | None = None


@router.get("/approvals")
async def list_pending_approvals(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: str = Query("pending"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List email drafts awaiting operator review."""
    q = (
        select(OutreachApproval)
        .where(OutreachApproval.status == status_filter)
        .options(
            selectinload(OutreachApproval.lead).selectinload(Lead.prospect),
            selectinload(OutreachApproval.lead).selectinload(Lead.campaign),
            selectinload(OutreachApproval.lead).selectinload(Lead.research),
            selectinload(OutreachApproval.lead).selectinload(Lead.score),
        )
        .order_by(OutreachApproval.created_at.desc())
    )

    total = await db.scalar(
        select(func.count(OutreachApproval.id)).where(OutreachApproval.status == status_filter)
    )
    res = await db.execute(q.offset((page - 1) * page_size).limit(page_size))
    items = res.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": str(appr.id),
                "lead_id": str(appr.lead_id),
                "subject": appr.subject,
                "body": appr.body,
                "status": appr.status,
                "created_at": appr.created_at.isoformat(),
                "prospect": {
                    "full_name": appr.lead.prospect.full_name if appr.lead and appr.lead.prospect else "Unknown",
                    "title": appr.lead.prospect.title if appr.lead and appr.lead.prospect else "",
                    "email": appr.lead.prospect.email if appr.lead and appr.lead.prospect else "",
                },
                "company_name": appr.lead.prospect.company.name if appr.lead and appr.lead.prospect and appr.lead.prospect.company else "",
                "campaign_name": appr.lead.campaign.name if appr.lead and appr.lead.campaign else "",
                "score": appr.lead.score.total_score if appr.lead and appr.lead.score else None,
                "why_rayven": appr.lead.research.why_rayven_relevant if appr.lead and appr.lead.research else None,
            }
            for appr in items
        ],
    }


@router.post("/approvals/{approval_id}/approve")
async def approve_outreach_draft(
    approval_id: uuid.UUID,
    body: ApprovalActionRequest | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Approve a draft (optionally with edits) and send/queue it."""
    appr = await db.get(OutreachApproval, approval_id)
    if not appr:
        raise HTTPException(status_code=404, detail="Approval request not found")

    if body and body.subject:
        appr.subject = body.subject
    if body and body.body:
        appr.body = body.body

    appr.status = "approved"
    appr.reviewed_by_id = current_user.id
    appr.reviewed_at = datetime.now(UTC)

    # Trigger send via OutreachService
    from app.providers.registry import get_email_provider
    from app.services.outreach import OutreachService
    service = OutreachService(db)
    provider = get_email_provider()

    result = await service.send_lead_message(
        lead_id=appr.lead_id,
        email_provider=provider,
    )

    db.add(AuditLog(
        user_id=current_user.id,
        action=AuditAction.HUMAN_REPLIED,
        resource_type="outreach_approval",
        resource_id=str(approval_id),
        details={"result": result},
    ))
    await db.commit()
    return {"status": "approved", "send_result": result}


@router.post("/approvals/{approval_id}/reject")
async def reject_outreach_draft(
    approval_id: uuid.UUID,
    body: ApprovalActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reject a draft — stops outreach for this lead."""
    appr = await db.get(OutreachApproval, approval_id)
    if not appr:
        raise HTTPException(status_code=404, detail="Approval request not found")

    appr.status = "rejected"
    appr.rejection_reason = body.rejection_reason or "Rejected by operator"
    appr.reviewed_by_id = current_user.id
    appr.reviewed_at = datetime.now(UTC)

    lead = await db.get(Lead, appr.lead_id)
    if lead:
        lead.is_stopped = True
        lead.stopped_reason = f"Draft rejected: {appr.rejection_reason}"
        lead.status = LeadStatus.NOT_INTERESTED

    await db.commit()
    return {"status": "rejected", "approval_id": str(approval_id)}
