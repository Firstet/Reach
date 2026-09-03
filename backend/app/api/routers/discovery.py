"""Lead Discovery API endpoints."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routers.auth import get_current_user
from app.core.database import get_db
from app.models import AuditAction, AuditLog, Campaign, DiscoveryJob, User

router = APIRouter(prefix="/discovery", tags=["discovery"])


class CSVImportRequest(BaseModel):
    campaign_id: uuid.UUID
    rows: list[dict[str, Any]]


class DiscoverTriggerRequest(BaseModel):
    campaign_id: uuid.UUID
    query: str | None = None


@router.post("/trigger", status_code=202)
async def trigger_discovery(
    body: DiscoverTriggerRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger background lead discovery for a campaign."""
    campaign = await db.get(Campaign, body.campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    query_text = body.query or campaign.discovery_query or f"Find target leaders for {campaign.name}"

    job = DiscoveryJob(
        id=uuid.uuid4(),
        campaign_id=campaign.id,
        status="pending",
        query=query_text,
    )
    db.add(job)
    db.add(AuditLog(
        user_id=current_user.id,
        action=AuditAction.AGENT_STARTED,
        resource_type="discovery_job",
        resource_id=str(job.id),
        details={"campaign_id": str(campaign.id), "query": query_text},
    ))
    await db.commit()

    from app.agents.discovery_agent import run_discovery_agent

    async def _async_run():
        async with db.begin():
            await run_discovery_agent(db, campaign.id, job.id)

    background_tasks.add_task(run_discovery_agent, db, campaign.id, job.id)
    return {"job_id": str(job.id), "status": "pending", "query": query_text}


@router.get("/jobs/{job_id}")
async def get_discovery_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = await db.get(DiscoveryJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Discovery job not found")
    return {
        "id": str(job.id),
        "campaign_id": str(job.campaign_id),
        "status": job.status,
        "query": job.query,
        "results_count": job.results_count,
        "error_message": job.error_message,
        "created_at": job.created_at.isoformat(),
    }


@router.post("/import-csv", status_code=201)
async def import_csv_prospects(
    body: CSVImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Bulk import prospects from CSV rows into a campaign."""
    campaign = await db.get(Campaign, body.campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    from app.services.discovery import DiscoveryService
    service = DiscoveryService(db)

    created_ids = await service.ingest_csv_prospects(body.rows, campaign.id)

    db.add(AuditLog(
        user_id=current_user.id,
        action=AuditAction.LEAD_CREATED,
        resource_type="campaign",
        resource_id=str(campaign.id),
        details={"imported_count": len(created_ids), "source": "csv_import"},
    ))
    await db.commit()
    return {"imported": len(created_ids), "lead_ids": [str(i) for i in created_ids]}
