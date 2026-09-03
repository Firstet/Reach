"""Suppression & Blocklist API router."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routers.auth import get_current_user
from app.core.database import get_db
from app.models import Suppression, User
from app.services.safety import SafetyService

router = APIRouter(tags=["suppression"])


class SuppressionCreate(BaseModel):
    suppression_type: str  # "email" | "domain"
    value: str
    reason: str | None = None


# ── Operator Blocklist Management Routes ──────────────────────────────────────

admin_router = APIRouter(prefix="/suppression", tags=["suppression"])


@admin_router.get("")
async def list_suppressions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    res = await db.execute(select(Suppression).order_by(Suppression.created_at.desc()))
    items = res.scalars().all()
    return {
        "items": [
            {
                "id": str(s.id),
                "suppression_type": s.suppression_type,
                "value": s.value,
                "reason": s.reason,
                "created_at": s.created_at.isoformat(),
            }
            for s in items
        ]
    }


@admin_router.post("", status_code=201)
async def add_suppression(
    body: SuppressionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    clean_val = body.value.lower().strip()
    sup = Suppression(
        id=uuid.uuid4(),
        suppression_type=body.suppression_type.lower(),
        value=clean_val,
        reason=body.reason,
        added_by_id=current_user.id,
    )
    db.add(sup)
    await db.commit()
    return {"id": str(sup.id), "value": clean_val}


@admin_router.delete("/{suppression_id}")
async def remove_suppression(
    suppression_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sup = await db.get(Suppression, suppression_id)
    if not sup:
        raise HTTPException(status_code=404, detail="Suppression entry not found")
    await db.delete(sup)
    await db.commit()
    return {"deleted": True}


# ── Public Unsubscribe Link Handler ───────────────────────────────────────────

@router.get("/suppression/unsubscribe", response_class=HTMLResponse)
async def public_unsubscribe_link(
    p: str = Query(..., description="Prospect ID"),
    db: AsyncSession = Depends(get_db),
):
    """Public endpoint embedded in email footer — unsubscribes prospect instantly."""
    service = SafetyService(db)
    success = await service.unsubscribe_prospect(p, reason="clicked_unsubscribe_link")

    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Unsubscribed — Rayven Strategic Communications</title>
    <style>
        body { background-color: #0a0a0f; color: #f0f0f5; font-family: -apple-system, sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
        .card { background: #16161f; border: 1px solid #2a2a38; border-radius: 12px; padding: 40px; text-align: center; max-width: 400px; }
        h1 { color: #c9a84c; font-size: 20px; margin-bottom: 12px; }
        p { color: #9090a8; font-size: 14px; line-height: 1.5; }
    </style>
</head>
<body>
    <div class="card">
        <h1>Unsubscribed</h1>
        <p>You have been successfully unsubscribed from Rayven Strategic Communications outreach.</p>
        <p style="font-size: 12px; color: #5a5a72; margin-top: 24px;">No further emails will be sent to your address.</p>
    </div>
</body>
</html>
"""
    return HTMLResponse(content=html_content)
