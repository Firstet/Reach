"""Company and Prospect CRUD routes."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routers.auth import get_current_user
from app.core.database import get_db
from app.models import Company, Prospect, User

router = APIRouter(tags=["prospects"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class CompanyCreate(BaseModel):
    name: str
    domain: str | None = None
    website: str | None = None
    industry: str | None = None
    sub_industry: str | None = None
    size: str | None = None
    employee_count: int | None = None
    country: str | None = None
    city: str | None = None
    description: str | None = None
    linkedin_url: str | None = None


class ProspectCreate(BaseModel):
    company_id: uuid.UUID | None = None
    first_name: str
    last_name: str
    email: str | None = None
    title: str | None = None
    seniority: str | None = None
    department: str | None = None
    linkedin_url: str | None = None
    location: str | None = None
    source: str | None = None


def _company_dict(c: Company) -> dict:
    return {
        "id": str(c.id),
        "name": c.name,
        "domain": c.domain,
        "website": c.website,
        "industry": c.industry,
        "sub_industry": c.sub_industry,
        "size": c.size,
        "employee_count": c.employee_count,
        "country": c.country,
        "city": c.city,
        "description": c.description,
        "linkedin_url": c.linkedin_url,
        "source": c.source,
        "research_summary": c.research_summary,
        "created_at": c.created_at.isoformat(),
    }


def _prospect_dict(p: Prospect) -> dict:
    return {
        "id": str(p.id),
        "company_id": str(p.company_id) if p.company_id else None,
        "first_name": p.first_name,
        "last_name": p.last_name,
        "full_name": p.full_name,
        "email": p.email,
        "email_confidence": p.email_confidence,
        "email_verified": p.email_verified,
        "email_status": p.email_status,
        "title": p.title,
        "seniority": p.seniority,
        "department": p.department,
        "linkedin_url": p.linkedin_url,
        "location": p.location,
        "source": p.source,
        "is_unsubscribed": p.is_unsubscribed,
        "research_summary": p.research_summary,
        "created_at": p.created_at.isoformat(),
    }


# ── Company Routes ────────────────────────────────────────────────────────────

companies_router = APIRouter(prefix="/companies")


@companies_router.get("")
async def list_companies(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    industry: str | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = select(Company)
    if industry:
        q = q.where(Company.industry.ilike(f"%{industry}%"))
    if search:
        q = q.where(Company.name.ilike(f"%{search}%"))
    q = q.order_by(Company.name)

    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    result = await db.execute(q.offset((page - 1) * page_size).limit(page_size))
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [_company_dict(c) for c in result.scalars().all()],
    }


@companies_router.post("", status_code=201)
async def create_company(
    body: CompanyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = Company(id=uuid.uuid4(), **body.model_dump())
    db.add(company)
    await db.commit()
    return _company_dict(company)


@companies_router.get("/{company_id}")
async def get_company(
    company_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return _company_dict(company)


# ── Prospect Routes ───────────────────────────────────────────────────────────

prospects_router = APIRouter(prefix="/prospects")


@prospects_router.get("")
async def list_prospects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    company_id: uuid.UUID | None = None,
    search: str | None = None,
    has_email: bool | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = select(Prospect)
    if company_id:
        q = q.where(Prospect.company_id == company_id)
    if search:
        q = q.where(
            (Prospect.first_name + " " + Prospect.last_name).ilike(f"%{search}%")
        )
    if has_email is True:
        q = q.where(Prospect.email.isnot(None))
    elif has_email is False:
        q = q.where(Prospect.email.is_(None))

    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    result = await db.execute(q.offset((page - 1) * page_size).limit(page_size))
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [_prospect_dict(p) for p in result.scalars().all()],
    }


@prospects_router.post("", status_code=201)
async def create_prospect(
    body: ProspectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prospect = Prospect(id=uuid.uuid4(), **body.model_dump())
    db.add(prospect)
    await db.commit()
    return _prospect_dict(prospect)


@prospects_router.get("/{prospect_id}")
async def get_prospect(
    prospect_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Prospect).where(Prospect.id == prospect_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Prospect not found")
    return _prospect_dict(p)
