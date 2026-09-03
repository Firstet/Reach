"""Test Mode & Simulation API router."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routers.auth import get_current_user
from app.core.database import get_db
from app.models import Campaign, Lead, Prospect, User
from app.providers.registry import get_llm_provider
from app.services.conversation import ConversationService
from app.services.discovery import DiscoveryService
from app.services.personalization import PersonalizationService

router = APIRouter(prefix="/test", tags=["test_mode"])


class SimulateReplyRequest(BaseModel):
    lead_id: uuid.UUID
    reply_text: str
    subject: str | None = None


class PreviewEmailRequest(BaseModel):
    lead_id: uuid.UUID
    step_number: int = 1


@router.post("/simulate-discovery/{campaign_id}")
async def simulate_discovery(
    campaign_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Simulate lead discovery by generating 3 realistic test prospects."""
    campaign = await db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    service = DiscoveryService(db)
    test_prospects = [
        {"first_name": "Amina", "last_name": "Bello", "title": "Chief Executive Officer", "company": "PayWave Tech", "domain": "paywavetech.ng", "industry": "Finance", "email": "amina.bello@paywavetech.ng"},
        {"first_name": "Emeka", "last_name": "Okonkwo", "title": "Chief Marketing Officer", "company": "Apex Health Systems", "domain": "apexhealth.ng", "industry": "Healthcare", "email": "emeka.o@apexhealth.ng"},
        {"first_name": "Tunde", "last_name": "Adeyemi", "title": "Head of Corporate Communications", "company": "Kestrel Energy Africa", "domain": "kestrelenergy.com", "industry": "Energy", "email": "tadeyemi@kestrelenergy.com"},
    ]

    lead_ids = await service.ingest_csv_prospects(test_prospects, campaign.id)
    for lid in lead_ids:
        lead = await db.get(Lead, lid)
        if lead:
            lead.is_test = True

    await db.commit()
    return {"simulated": True, "lead_count": len(lead_ids), "lead_ids": [str(i) for i in lead_ids]}


@router.post("/simulate-reply")
async def simulate_prospect_reply(
    body: SimulateReplyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Simulate receiving an inbound reply from a prospect.
    Triggers sequence stopping, classification, and human escalation notification.
    """
    lead = await db.get(Lead, body.lead_id)
    if not lead or not lead.prospect:
        raise HTTPException(status_code=404, detail="Lead or prospect not found")

    prospect = lead.prospect
    if not prospect.email:
        raise HTTPException(status_code=400, detail="Prospect missing email address")

    llm = get_llm_provider()
    from app.providers.registry import get_notification_provider
    noti_provider = get_notification_provider()
    service = ConversationService(db)

    result = await service.process_inbound_reply(
        from_email=prospect.email,
        subject=body.subject or "Re: Strategic Communications",
        body_text=body.reply_text,
        provider_message_id=f"simulated-reply-{uuid.uuid4()}",
        llm=llm,
        notification_provider=noti_provider,
    )
    return {"simulated": True, "result": result}


@router.post("/preview-email")
async def preview_personalized_email(
    body: PreviewEmailRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate and return a personalized outreach email draft WITHOUT saving to DB."""
    lead = await db.get(Lead, body.lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    llm = get_llm_provider()
    service = PersonalizationService(db)
    outreach = await service.generate_outreach_email(lead.id, step_number=body.step_number, llm=llm)

    return {
        "lead_id": str(lead.id),
        "step_number": body.step_number,
        "subject": outreach.subject,
        "body_text": outreach.body_text,
        "body_html": outreach.body_html,
        "reasoning": outreach.reasoning,
    }
