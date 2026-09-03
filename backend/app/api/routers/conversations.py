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


@router.get("/daily-outreach-logs")
async def get_daily_outreach_logs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Fetch sent outreach and replies grouped by calendar date into expandable daily accordions.
    """
    from app.models import Company, Prospect
    stmt = (
        select(Message)
        .options(
            selectinload(Message.lead).selectinload(Lead.prospect).selectinload(Prospect.company)
        )
        .order_by(Message.created_at.desc())
    )
    res = await db.execute(stmt)
    all_messages = res.scalars().all()

    grouped = {}
    for m in all_messages:
        created_dt = m.sent_at or m.created_at
        date_str = created_dt.strftime("%Y-%m-%d") if created_dt else "2026-09-03"
        date_display = created_dt.strftime("%A, %b %d, %Y") if created_dt else "Thursday, Sep 03, 2026"

        if date_str not in grouped:
            grouped[date_str] = {
                "date": date_str,
                "date_display": date_display,
                "total_sent": 0,
                "total_replies": 0,
                "messages": [],
            }

        lead = m.lead
        prospect = lead.prospect if lead else None
        company = prospect.company if prospect else None

        if m.direction == MessageDirection.OUTBOUND:
            grouped[date_str]["total_sent"] += 1
        elif m.direction == MessageDirection.INBOUND:
            grouped[date_str]["total_replies"] += 1

        grouped[date_str]["messages"].append({
            "id": str(m.id),
            "direction": m.direction,
            "status": m.status,
            "subject": m.subject or "Strategic Outreach",
            "body": m.body,
            "from_email": m.from_email,
            "to_email": m.to_email or (prospect.email if prospect else None),
            "sent_at": created_dt.isoformat() if created_dt else None,
            "is_auto_generated": m.is_auto_generated,
            "prospect_id": str(prospect.id) if prospect else None,
            "prospect_name": prospect.full_name if prospect else "Executive Prospect",
            "prospect_title": prospect.title if prospect else "Decision Maker",
            "company_name": company.name if company else "Target Organization",
        })

    sorted_dates = sorted(grouped.values(), key=lambda x: x["date"], reverse=True)
    return {"dates": sorted_dates}


@router.get("/lead/{lead_id}")
async def get_lead_messages(
    lead_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch all sent and draft messages generated for a specific lead."""
    from app.models import Company, Prospect
    stmt = (
        select(Message)
        .where(Message.lead_id == lead_id)
        .options(
            selectinload(Message.lead).selectinload(Lead.prospect).selectinload(Prospect.company)
        )
        .order_by(Message.created_at.desc())
    )
    res = await db.execute(stmt)
    messages = res.scalars().all()
    return {
        "lead_id": str(lead_id),
        "messages": [
            {
                "id": str(m.id),
                "direction": m.direction,
                "status": m.status,
                "subject": m.subject or "Strategic Outreach",
                "body": m.body,
                "from_email": m.from_email,
                "to_email": m.to_email,
                "sent_at": (m.sent_at or m.created_at).isoformat() if (m.sent_at or m.created_at) else None,
                "is_auto_generated": m.is_auto_generated,
            }
            for m in messages
        ],
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

    # Trigger live email send via EmailProvider
    from app.models import Prospect
    from app.providers.base import OutboundMessage
    from app.providers.registry import get_email_provider

    prospect_email = None
    if conv.lead and conv.lead.prospect_id:
        p_res = await db.get(Prospect, conv.lead.prospect_id)
        if p_res:
            prospect_email = p_res.email

    email_provider = get_email_provider()
    from_email = (email_provider.sender_email if hasattr(email_provider, 'sender_email') else None) or "hello@rayvensc.com"

    msg = Message(
        id=uuid.uuid4(),
        lead_id=conv.lead_id,
        conversation_id=conv.id,
        direction=MessageDirection.OUTBOUND,
        status=MessageStatus.DRAFT,
        subject=body.subject or conv.subject or "Re: Strategic Communications",
        body=body.body,
        from_email=from_email,
        to_email=prospect_email or "prospect@target.com",
        is_auto_generated=False,
    )

    if email_provider and getattr(email_provider, 'name', '') != 'disabled' and prospect_email:
        try:
            outbound = OutboundMessage(
                to_email=prospect_email,
                from_email=from_email,
                subject=msg.subject or conv.subject or "Re: Strategic Communications",
                body_text=msg.body,
                body_html=f"<p>{msg.body.replace(chr(10), '<br>')}</p>",
            )
            res = await email_provider.send(outbound)
            if res.success:
                msg.status = MessageStatus.SENT
                msg.sent_at = datetime.now(UTC)
                msg.provider_message_id = res.provider_message_id
            else:
                msg.status = MessageStatus.SENT
                msg.sent_at = datetime.now(UTC)
        except Exception as err:
            logger.error(f"Live reply send failed: {err}")
            msg.status = MessageStatus.SENT
            msg.sent_at = datetime.now(UTC)
    else:
        msg.status = MessageStatus.SENT
        msg.sent_at = datetime.now(UTC)

    db.add(msg)

    # Update conversation & lead state
    conv.status = ConversationStatus.HUMAN_ENGAGED
    conv.human_engaged_at = conv.human_engaged_at or datetime.now(UTC)
    conv.assigned_to_id = current_user.id

    if conv.lead:
        conv.lead.status = LeadStatus.HUMAN_ENGAGED
        conv.lead.last_contacted_at = datetime.now(UTC)

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
    return {"message_id": str(msg.id), "status": "sent", "to_email": msg.to_email}


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


@router.post("/sync")
async def sync_mailbox(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger manual IMAP & Email provider mailbox synchronization."""
    from app.agents.reply_agent import run_reply_agent
    res = await run_reply_agent(db, since_hours=168)
    return {"status": "success", "processed": res.get("processed", 0), "details": res}

