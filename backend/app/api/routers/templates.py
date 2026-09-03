"""Email Templates library API router."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routers.auth import get_current_user
from app.core.database import get_db
from app.models import EmailTemplate, User

router = APIRouter(prefix="/templates", tags=["templates"])


class TemplateCreate(BaseModel):
    name: str
    category: str = "outreach"
    subject_template: str
    body_template: str
    variables: list[str] = []


class TemplateUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    subject_template: str | None = None
    body_template: str | None = None
    is_active: bool | None = None


def _tmpl_dict(t: EmailTemplate) -> dict:
    return {
        "id": str(t.id),
        "name": t.name,
        "category": t.category,
        "subject_template": t.subject_template,
        "body_template": t.body_template,
        "is_active": t.is_active,
        "variables": t.variables or [],
        "created_at": t.created_at.isoformat(),
    }


@router.get("")
async def list_templates(
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = select(EmailTemplate).where(EmailTemplate.is_active == True)
    if category:
        q = q.where(EmailTemplate.category == category)
    q = q.order_by(EmailTemplate.name)
    res = await db.execute(q)
    return {"items": [_tmpl_dict(t) for t in res.scalars().all()]}


@router.post("", status_code=201)
async def create_template(
    body: TemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tmpl = EmailTemplate(
        id=uuid.uuid4(),
        name=body.name,
        category=body.category,
        subject_template=body.subject_template,
        body_template=body.body_template,
        variables=body.variables,
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
    tmpl = await db.get(EmailTemplate, template_id)
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template not found")

    for k, v in body.model_dump(exclude_none=True).items():
        setattr(tmpl, k, v)

    await db.commit()
    return _tmpl_dict(tmpl)


@router.delete("/{template_id}")
async def delete_template(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tmpl = await db.get(EmailTemplate, template_id)
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template not found")
    tmpl.is_active = False
    await db.commit()
    return {"deleted": True}
