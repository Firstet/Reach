"""Scoring Engine configuration API router."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routers.auth import get_current_user
from app.core.database import get_db
from app.models import Campaign, Lead, User
from app.services.scoring import DEFAULT_SCORING_WEIGHTS, ScoringService

router = APIRouter(prefix="/scoring", tags=["scoring"])


class ScoringWeightsUpdate(BaseModel):
    seniority: float = 30.0
    industry_fit: float = 25.0
    communication_signal: float = 20.0
    email_confidence: float = 15.0
    company_size: float = 10.0


@router.get("/defaults")
async def get_default_scoring_weights(current_user: User = Depends(get_current_user)):
    """Return system-wide default scoring weights."""
    return {"weights": DEFAULT_SCORING_WEIGHTS}


@router.get("/campaigns/{campaign_id}")
async def get_campaign_scoring_config(
    campaign_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    campaign = await db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    return {
        "campaign_id": str(campaign_id),
        "min_score_threshold": campaign.min_score_threshold,
        "scoring_weights": campaign.scoring_weights or DEFAULT_SCORING_WEIGHTS,
    }


@router.put("/campaigns/{campaign_id}")
async def update_campaign_scoring_config(
    campaign_id: uuid.UUID,
    min_score_threshold: float | None = None,
    weights: ScoringWeightsUpdate | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    campaign = await db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if min_score_threshold is not None:
        campaign.min_score_threshold = min_score_threshold

    if weights:
        campaign.scoring_weights = weights.model_dump()

    await db.commit()
    return {
        "status": "updated",
        "min_score_threshold": campaign.min_score_threshold,
        "scoring_weights": campaign.scoring_weights,
    }


@router.post("/rescore/{lead_id}")
async def rescore_lead(
    lead_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manually trigger lead rescoring."""
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    service = ScoringService(db)
    score_obj = await service.score_lead(lead.id)

    return {
        "lead_id": str(lead_id),
        "total_score": score_obj.total_score,
        "is_qualified": score_obj.is_qualified,
        "reason": score_obj.qualification_reason,
    }
