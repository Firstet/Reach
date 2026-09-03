"""Lightweight CRM API router."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routers.auth import get_current_user
from app.core.database import get_db
from app.models import CRMStage, User
from app.services.crm import CRMService

router = APIRouter(prefix="/crm", tags=["crm"])


class StageUpdateRequest(BaseModel):
    new_stage: CRMStage
    notes: str | None = None


@router.get("/pipeline")
async def get_crm_pipeline(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch complete CRM pipeline summary and lead records categorized across 12 stages."""
    service = CRMService(db)
    return await service.get_crm_pipeline_summary()


@router.put("/leads/{lead_id}/stage")
async def update_lead_stage(
    lead_id: uuid.UUID,
    body: StageUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manually transition a lead to a new CRM stage."""
    service = CRMService(db)
    try:
        lead = await service.update_lead_crm_stage(
            lead_id=lead_id,
            new_stage=body.new_stage,
            operator_id=current_user.id,
            notes=body.notes,
        )
        return {
            "lead_id": str(lead.id),
            "new_stage": lead.crm_stage.value,
            "updated_at": lead.updated_at.isoformat(),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
