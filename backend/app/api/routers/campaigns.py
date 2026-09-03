"""Campaign CRUD routes."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.routers.auth import get_current_user
from app.core.database import get_db
from app.models import (
    AuditAction,
    AuditLog,
    Campaign,
    CampaignStatus,
    CampaignStep,
    Lead,
    User,
)

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class CampaignStepIn(BaseModel):
    step_order: int
    step_type: str = "email"
    subject_template: str | None = None
    body_template: str | None = None
    wait_hours: int | None = None


class CampaignCreate(BaseModel):
    name: str
    description: str | None = None
    target_industry: str | None = None
    target_company_size: str | None = None
    target_seniority: str | None = None
    target_location: str | None = None
    daily_send_limit: int = 50
    send_window_start: int = 9
    send_window_end: int = 17
    max_follow_ups: int = 3
    follow_up_delay_hours: int = 72
    value_proposition: str | None = None
    personalization_notes: str | None = None
    steps: list[CampaignStepIn] = []


class CampaignUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    target_industry: str | None = None
    target_company_size: str | None = None
    target_seniority: str | None = None
    target_location: str | None = None
    daily_send_limit: int | None = None
    send_window_start: int | None = None
    send_window_end: int | None = None
    max_follow_ups: int | None = None
    follow_up_delay_hours: int | None = None
    value_proposition: str | None = None
    personalization_notes: str | None = None


def _campaign_to_dict(c: Campaign, include_steps: bool = True) -> dict:
    d: dict[str, Any] = {
        "id": str(c.id),
        "name": c.name,
        "description": c.description,
        "status": c.status,
        "target_industry": c.target_industry,
        "target_company_size": c.target_company_size,
        "target_seniority": c.target_seniority,
        "target_location": c.target_location,
        "daily_send_limit": c.daily_send_limit,
        "send_window_start": c.send_window_start,
        "send_window_end": c.send_window_end,
        "max_follow_ups": c.max_follow_ups,
        "follow_up_delay_hours": c.follow_up_delay_hours,
        "value_proposition": c.value_proposition,
        "personalization_notes": c.personalization_notes,
        "started_at": c.started_at.isoformat() if c.started_at else None,
        "paused_at": c.paused_at.isoformat() if c.paused_at else None,
        "completed_at": c.completed_at.isoformat() if c.completed_at else None,
        "created_at": c.created_at.isoformat(),
        "updated_at": c.updated_at.isoformat(),
    }
    if include_steps and c.steps:
        d["steps"] = [
            {
                "id": str(s.id),
                "step_order": s.step_order,
                "step_type": s.step_type,
                "subject_template": s.subject_template,
                "body_template": s.body_template,
                "wait_hours": s.wait_hours,
            }
            for s in c.steps
        ]
    return d


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("")
async def list_campaigns(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: CampaignStatus | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = select(Campaign)
    if status:
        q = q.where(Campaign.status == status)
    q = q.order_by(Campaign.created_at.desc())

    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    q = q.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)
    campaigns = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [_campaign_to_dict(c, include_steps=False) for c in campaigns],
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_campaign(
    body: CampaignCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    campaign = Campaign(
        id=uuid.uuid4(),
        name=body.name,
        description=body.description,
        status=CampaignStatus.DRAFT,
        target_industry=body.target_industry,
        target_company_size=body.target_company_size,
        target_seniority=body.target_seniority,
        target_location=body.target_location,
        daily_send_limit=body.daily_send_limit,
        send_window_start=body.send_window_start,
        send_window_end=body.send_window_end,
        max_follow_ups=body.max_follow_ups,
        follow_up_delay_hours=body.follow_up_delay_hours,
        value_proposition=body.value_proposition,
        personalization_notes=body.personalization_notes,
        created_by_id=current_user.id,
    )
    db.add(campaign)
    await db.flush()

    for step_data in body.steps:
        db.add(CampaignStep(
            id=uuid.uuid4(),
            campaign_id=campaign.id,
            step_order=step_data.step_order,
            step_type=step_data.step_type,
            subject_template=step_data.subject_template,
            body_template=step_data.body_template,
            wait_hours=step_data.wait_hours,
        ))

    db.add(AuditLog(
        user_id=current_user.id,
        action=AuditAction.CAMPAIGN_CREATED,
        resource_type="campaign",
        resource_id=str(campaign.id),
    ))
    await db.commit()

    await db.refresh(campaign, ["steps"])
    return _campaign_to_dict(campaign)


@router.get("/{campaign_id}")
async def get_campaign(
    campaign_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Campaign)
        .where(Campaign.id == campaign_id)
        .options(selectinload(Campaign.steps))
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Include lead stats
    lead_count = await db.scalar(
        select(func.count(Lead.id)).where(Lead.campaign_id == campaign_id)
    )
    d = _campaign_to_dict(campaign)
    d["lead_count"] = lead_count
    return d


@router.put("/{campaign_id}")
async def update_campaign(
    campaign_id: uuid.UUID,
    body: CampaignUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if campaign.status == CampaignStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Cannot edit an active campaign. Pause it first.")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(campaign, field, value)

    await db.commit()
    return _campaign_to_dict(campaign)


@router.post("/{campaign_id}/start")
async def start_campaign(
    campaign_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if campaign.status == CampaignStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Campaign is already active")

    campaign.status = CampaignStatus.ACTIVE
    campaign.started_at = datetime.now(UTC)

    db.add(AuditLog(
        user_id=current_user.id,
        action=AuditAction.CAMPAIGN_STARTED,
        resource_type="campaign",
        resource_id=str(campaign.id),
    ))
    await db.commit()
    return {"status": "active", "campaign_id": str(campaign_id)}


@router.post("/{campaign_id}/pause")
async def pause_campaign(
    campaign_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    campaign.status = CampaignStatus.PAUSED
    campaign.paused_at = datetime.now(UTC)

    db.add(AuditLog(
        user_id=current_user.id,
        action=AuditAction.CAMPAIGN_PAUSED,
        resource_type="campaign",
        resource_id=str(campaign.id),
    ))
    await db.commit()
    return {"status": "paused", "campaign_id": str(campaign_id)}
