"""Conversation inbox and thread routes."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.routers.auth import get_current_user
from app.core.database import get_db
from app.models import (
    AuditAction,
    AuditLog,
    Conversation,
    ConversationEvent,
    ConversationStatus,
    Lead,
    LeadStatus,
    Message,
    MessageDirection,
    MessageStatus,
    Notification,
    NotificationStatus,
    User,
)

router = APIRouter(prefix="/conversations", tags=["conversations"])


class HumanReplyRequest(BaseModel):
    body: str
    subject: str | None = None


def _conversation_dict(c: Conversation) -> dict:
    return {
        "id": str(c.id),
        "lead_id": str(c.lead_id),
        "status": c.status,
        "subject": c.subject,
        "last_reply_intent": c.last_reply_intent,
        "escalated_at": c.escalated_at.isoformat() if c.escalated_at else None,
        "human_engaged_at": c.human_engaged_at.isoformat() if c.human_engaged_at else None,
        "resolved_at": c.resolved_at.isoformat() if c.resolved_at else None,
        "assigned_to_id": str(c.assigned_to_id) if c.assigned_to_id else None,
        "message_count": len(c.messages) if c.messages else 0,
        "created_at": c.created_at.isoformat(),
        "updated_at": c.updated_at.isoformat(),
    }


def _message_dict(m: Message) -> dict:
    return {
        "id": str(m.id),
        "direction": m.direction,
        "status": m.status,
        "subject": m.subject,
        "body": m.body,
        "from_email": m.from_email,
        "to_email": m.to_email,
        "sent_at": m.sent_at.isoformat() if m.sent_at else None,
        "is_auto_generated": m.is_auto_generated,
        "created_at": m.created_at.isoformat(),
    }


@router.get("")
async def list_conversations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: ConversationStatus | None = None,
    escalated_only: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = select(Conversation).options(selectinload(Conversation.messages))
    if status:
        q = q.where(Conversation.status == status)
    if escalated_only:
        q = q.where(Conversation.status.in_([
            ConversationStatus.ESCALATED,
            ConversationStatus.HUMAN_ENGAGED,
        ]))
    q = q.order_by(Conversation.updated_at.desc())

    total = await db.scalar(select(func.count(Conversation.id)))
    result = await db.execute(q.offset((page - 1) * page_size).limit(page_size))

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [_conversation_dict(c) for c in result.scalars().all()],
    }


@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .options(
            selectinload(Conversation.messages),
            selectinload(Conversation.events),
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    d = _conversation_dict(conv)
    d["messages"] = [_message_dict(m) for m in conv.messages]
    d["events"] = [
        {
            "id": str(e.id),
            "event_type": e.event_type,
            "actor": e.actor,
            "details": e.details,
            "created_at": e.created_at.isoformat(),
        }
        for e in conv.events
    ]
    return d


@router.post("/{conversation_id}/reply")
async def human_reply(
    conversation_id: uuid.UUID,
    body: HumanReplyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Human operator sends a reply from the dashboard."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .options(selectinload(Conversation.lead))
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Create message record (actual sending is done via email provider in Phase 2)
    msg = Message(
        id=uuid.uuid4(),
        lead_id=conv.lead_id,
        conversation_id=conv.id,
        direction=MessageDirection.OUTBOUND,
        status=MessageStatus.DRAFT,  # Will be SENT once email provider sends
        subject=body.subject or conv.subject,
        body=body.body,
        is_auto_generated=False,
    )
    db.add(msg)

    # Update conversation state
    conv.status = ConversationStatus.HUMAN_ENGAGED
    conv.human_engaged_at = conv.human_engaged_at or datetime.now(UTC)
    conv.assigned_to_id = current_user.id

    # Event
    db.add(ConversationEvent(
        id=uuid.uuid4(),
        conversation_id=conv.id,
        event_type="human_replied",
        actor="human",
        actor_id=current_user.id,
    ))

    db.add(AuditLog(
        user_id=current_user.id,
        action=AuditAction.HUMAN_REPLIED,
        resource_type="conversation",
        resource_id=str(conv.id),
    ))
    await db.commit()
    return {"message_id": str(msg.id), "status": "queued"}


@router.post("/{conversation_id}/escalate")
async def escalate_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conv.status = ConversationStatus.ESCALATED
    conv.escalated_at = datetime.now(UTC)

    # Stop automated outreach for this lead
    lead_result = await db.execute(select(Lead).where(Lead.id == conv.lead_id))
    lead = lead_result.scalar_one_or_none()
    if lead:
        lead.is_stopped = True
        lead.stopped_reason = "escalated_to_human"
        lead.status = LeadStatus.ESCALATED

    db.add(ConversationEvent(
        id=uuid.uuid4(),
        conversation_id=conv.id,
        event_type="manually_escalated",
        actor="human",
        actor_id=current_user.id,
    ))
    db.add(AuditLog(
        user_id=current_user.id,
        action=AuditAction.CONVERSATION_ESCALATED,
        resource_type="conversation",
        resource_id=str(conv.id),
    ))
    await db.commit()
    return {"status": "escalated", "conversation_id": str(conversation_id)}


@router.post("/{conversation_id}/resolve")
async def resolve_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conv.status = ConversationStatus.CLOSED
    conv.resolved_at = datetime.now(UTC)

    db.add(ConversationEvent(
        id=uuid.uuid4(),
        conversation_id=conv.id,
        event_type="resolved",
        actor="human",
        actor_id=current_user.id,
    ))
    await db.commit()
    return {"status": "resolved", "conversation_id": str(conversation_id)}


@router.post("/{conversation_id}/takeover")
async def takeover_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Operator takes full control of thread, disabling AI auto-reply."""
    from app.services.handoff import HumanHandoffService
    service = HumanHandoffService(db)
    conv = await service.take_over_conversation(conversation_id, current_user.id)
    return {"status": "human_takeover", "conversation_id": str(conv.id), "ai_auto_respond": False}


@router.post("/{conversation_id}/return-to-ai")
async def return_conversation_to_ai(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Operator returns thread to AI automated monitoring."""
    from app.services.handoff import HumanHandoffService
    service = HumanHandoffService(db)
    conv = await service.return_to_ai(conversation_id, current_user.id)
    return {"status": "ai_monitoring", "conversation_id": str(conv.id), "ai_auto_respond": True}


@router.get("/{conversation_id}/copilot")
async def get_copilot_recommendations(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch private AI Copilot intelligence dossier, response variations, and meeting prep."""
    from app.providers.registry import get_llm_provider
    from app.services.copilot import AICopilotService
    service = AICopilotService(db)
    llm = get_llm_provider()
    dossier = await service.generate_copilot_dossier(conversation_id, llm)
    return {
        "conversation_summary": dossier.conversation_summary,
        "recommended_replies": dossier.recommended_replies,
        "objection_handling": dossier.objection_handling,
        "meeting_prep_questions": dossier.meeting_prep_questions,
        "relevant_rayven_services": dossier.relevant_rayven_services,
        "key_insights": dossier.key_insights,
    }

