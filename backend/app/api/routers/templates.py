"""
Email Templates library API router supporting the 15 RayvenSC Strategic Frameworks.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routers.auth import get_current_user
from app.core.database import get_db
from app.models import Campaign, EmailTemplate, User
from app.db.seed_templates import seed_email_templates

router = APIRouter(prefix="/templates", tags=["templates"])


class TemplateCreate(BaseModel):
    name: str
    category: str = "Initial Outreach"
    purpose: str | None = None
    when_to_use: str | None = None
    when_not_to_use: str | None = None
    recommended_lead_types: str | None = None
    subject_template: str
    body_template: str
    rules: str | None = None
    tone: str = "Consultative & Direct"
    max_length: str = "150 words"
    cta_style: str = "Low-pressure conversational"
    follow_up_rules: str | None = None
    is_active: bool = True
    variables: list[str] = []
    rayven_capabilities: list[str] = []


class TemplateUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    purpose: str | None = None
    when_to_use: str | None = None
    when_not_to_use: str | None = None
    recommended_lead_types: str | None = None
    subject_template: str | None = None
    body_template: str | None = None
    rules: str | None = None
    tone: str | None = None
    max_length: str | None = None
    cta_style: str | None = None
    follow_up_rules: str | None = None
    is_active: bool | None = None
    variables: list[str] | None = None
    rayven_capabilities: list[str] | None = None


class RecommendRequest(BaseModel):
    company_name: str | None = None
    industry: str | None = None
    job_title: str | None = None
    signal: str | None = None  # e.g., "expanding geographically", "founder active speaker", "new launch"
    step_number: int = 1


def _tmpl_dict(t: EmailTemplate) -> dict:
    return {
        "id": str(t.id),
        "slug": t.slug,
        "name": t.name,
        "category": t.category,
        "purpose": t.purpose or "",
        "when_to_use": t.when_to_use or "",
        "when_not_to_use": t.when_not_to_use or "",
        "recommended_lead_types": t.recommended_lead_types or "",
        "subject_template": t.subject_template,
        "body_template": t.body_template,
        "rules": t.rules or "",
        "tone": t.tone or "Consultative & Direct",
        "max_length": t.max_length or "150 words",
        "cta_style": t.cta_style or "Low-pressure conversational",
        "follow_up_rules": t.follow_up_rules or "",
        "is_active": t.is_active,
        "variables": t.variables or [],
        "rayven_capabilities": t.rayven_capabilities or [],
        "created_at": t.created_at.isoformat() if t.created_at else "",
        "updated_at": t.updated_at.isoformat() if t.updated_at else "",
    }


@router.get("")
async def list_templates(
    category: str | None = None,
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all email templates in the library."""
    # Ensure templates are seeded if table is empty
    q_check = select(EmailTemplate)
    res_check = await db.execute(q_check)
    if len(res_check.scalars().all()) == 0:
        await seed_email_templates(db)

    q = select(EmailTemplate)
    if not include_inactive:
        q = q.where(EmailTemplate.is_active == True)
    if category and category != "all":
        q = q.where(EmailTemplate.category == category)
    
    q = q.order_by(EmailTemplate.name)
    res = await db.execute(q)
    return {"items": [_tmpl_dict(t) for t in res.scalars().all()]}


@router.get("/{template_id}")
async def get_template(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single template by ID."""
    tmpl = await db.get(EmailTemplate, template_id)
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template framework not found")
    return _tmpl_dict(tmpl)


@router.post("", status_code=201)
async def create_template(
    body: TemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new custom strategic outreach template."""
    tmpl = EmailTemplate(
        id=uuid.uuid4(),
        slug=body.name.lower().replace(" ", "_").replace("/", "_"),
        name=body.name,
        category=body.category,
        purpose=body.purpose,
        when_to_use=body.when_to_use,
        when_not_to_use=body.when_not_to_use,
        recommended_lead_types=body.recommended_lead_types,
        subject_template=body.subject_template,
        body_template=body.body_template,
        rules=body.rules,
        tone=body.tone,
        max_length=body.max_length,
        cta_style=body.cta_style,
        follow_up_rules=body.follow_up_rules,
        is_active=body.is_active,
        variables=body.variables,
        rayven_capabilities=body.rayven_capabilities,
        created_by_id=current_user.id,
    )
    db.add(tmpl)
    await db.commit()
    return _tmpl_dict(tmpl)


@router.put("/{template_id}")
async def update_template(
    template_id: uuid.UUID,
    body: TemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an existing strategic template."""
    tmpl = await db.get(EmailTemplate, template_id)
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template not found")

    for k, v in body.model_dump(exclude_none=True).items():
        setattr(tmpl, k, v)

    await db.commit()
    return _tmpl_dict(tmpl)


@router.post("/{template_id}/duplicate", status_code=201)
async def duplicate_template(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Duplicate an existing template framework."""
    source = await db.get(EmailTemplate, template_id)
    if not source:
        raise HTTPException(status_code=404, detail="Template not found")

    cloned = EmailTemplate(
        id=uuid.uuid4(),
        slug=f"{source.slug}_copy",
        name=f"{source.name} (Copy)",
        category=source.category,
        purpose=source.purpose,
        when_to_use=source.when_to_use,
        when_not_to_use=source.when_not_to_use,
        recommended_lead_types=source.recommended_lead_types,
        subject_template=source.subject_template,
        body_template=source.body_template,
        rules=source.rules,
        tone=source.tone,
        max_length=source.max_length,
        cta_style=source.cta_style,
        follow_up_rules=source.follow_up_rules,
        is_active=True,
        variables=source.variables,
        rayven_capabilities=source.rayven_capabilities,
        created_by_id=current_user.id,
    )
    db.add(cloned)
    await db.commit()
    return _tmpl_dict(cloned)


@router.post("/{template_id}/toggle")
async def toggle_template_status(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Activate or deactivate a template."""
    tmpl = await db.get(EmailTemplate, template_id)
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template not found")
    tmpl.is_active = not tmpl.is_active
    await db.commit()
    return _tmpl_dict(tmpl)


@router.delete("/{template_id}")
async def delete_template(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Permanently delete a custom template."""
    tmpl = await db.get(EmailTemplate, template_id)
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template not found")
    await db.delete(tmpl)
    await db.commit()
    return {"deleted": True}


@router.post("/recommend")
async def recommend_template(
    body: RecommendRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    AI Template Selection Engine:
    Automatically recommends the most appropriate strategic outreach template framework based on prospect research.
    """
    sig = (body.signal or "").lower()
    role = (body.job_title or "").lower()
    step = body.step_number

    recommended_slug = "strategic_observation"

    if step == 2:
        recommended_slug = "followup_new_insight"
    elif step == 3:
        recommended_slug = "followup_strategic_idea"
    elif step == 4:
        recommended_slug = "followup_value_offer"
    elif step >= 5:
        recommended_slug = "breakup_close_loop"
    else: # Step 1 Initial Outreach
        if any(w in sig for w in ["expand", "growth", "new market", "acquisition", "scaling"]):
            recommended_slug = "growth_expansion"
        elif any(w in sig for w in ["speaker", "founder", "thought leader", "keynote", "author"]) or any(r in role for r in ["founder", "ceo", "managing director"]):
            recommended_slug = "personal_brand"
        elif any(w in sig for w in ["launch", "new product", "service", "initiative"]):
            recommended_slug = "product_service_launch"
        elif any(w in sig for w in ["positioning", "rebranding", "differentiation"]):
            recommended_slug = "brand_positioning"
        elif any(w in sig for w in ["digital", "marketing", "campaign", "social"]):
            recommended_slug = "digital_growth"
        elif any(w in sig for w in ["csr", "esg", "sustainability", "social impact"]):
            recommended_slug = "social_impact_csr"
        elif any(w in sig for w in ["market entry", "africa", "regional", "territory"]):
            recommended_slug = "market_entry"
        elif any(w in role for r in ["ceo", "c-suite", "board", "executive"]):
            recommended_slug = "executive_communication"
        elif any(w in sig for w in ["market research", "competitor", "trend"]):
            recommended_slug = "market_intelligence"
        elif any(w in sig for w in ["gap", "inconsistent", "unclear"]):
            recommended_slug = "communication_gap"

    stmt = select(EmailTemplate).where(EmailTemplate.slug == recommended_slug)
    res = await db.execute(stmt)
    matched = res.scalar_one_or_none()

    if not matched:
        # Fallback to first available active template
        res_fallback = await db.execute(select(EmailTemplate).where(EmailTemplate.is_active == True))
        matched = res_fallback.scalars().first()

    return {
        "recommended_slug": recommended_slug,
        "rationale": f"Selected framework '{matched.name if matched else recommended_slug}' based on signal analysis ('{body.signal or 'standard leadership prospect'}') and step #{step}.",
        "template": _tmpl_dict(matched) if matched else None,
    }


@router.post("/{template_id}/assign-campaign")
async def assign_template_to_campaign(
    template_id: uuid.UUID,
    campaign_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Assign a strategic framework template to a campaign."""
    tmpl = await db.get(EmailTemplate, template_id)
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template not found")
    
    camp = await db.get(Campaign, campaign_id)
    if not camp:
        raise HTTPException(status_code=404, detail="Campaign not found")

    camp.value_proposition = f"Framework: {tmpl.name}\nObjective: {tmpl.purpose}\n\nSubject Pattern: {tmpl.subject_template}\n\nBody Framework:\n{tmpl.body_template}\n\nRules:\n{tmpl.rules}"
    await db.commit()
    return {"assigned": True, "campaign_id": str(camp.id), "template": tmpl.name}
