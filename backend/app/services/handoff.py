"""
Human Handoff Service
Orchestrates takeover state transitions, sequence halting, AI auto-reply toggling,
and notification packet generation when leads become HOT or escalate.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    AuditAction,
    AuditLog,
    Conversation,
    ConversationEvent,
    ConversationStatus,
    CRMStage,
    Lead,
    LeadStatus,
    Message,
    MessageDirection,
    Prospect,
    User,
)
from app.providers.base import NotificationEvent, NotificationProvider
from app.services.outreach import OutreachService

logger = logging.getLogger(__name__)


class HumanHandoffService:
    """Manages human takeover, AI copilot activation, and escalation state transitions."""

    def __init__(self, session: AsyncSession):
        self._db = session
        self._outreach = OutreachService(session)

    async def escalate_hot_lead(
        self,
        lead_id: uuid.UUID,
        reason: str,
        intent_score: float = 90.0,
        notification_provider: NotificationProvider | None = None,
    ) -> dict:
        """
        Escalate a lead to HOT / Human Takeover.
        1. Halt automated sequence.
        2. Turn off AI auto-replies.
        3. Set LeadStatus -> ESCALATED, CRMStage -> HOT.
        4. Broadcast WebSocket / Email notification to Rayven operators.
        """
        lead = await self._db.get(Lead, lead_id)
        if not lead or not lead.prospect:
            raise ValueError(f"Lead {lead_id} missing prospect")

        # 1. Stop automated sequence
        await self._outreach.stop_automated_sequence(lead.id, reason=f"Hot Lead Escalation: {reason}")

        # 2. Update Lead & CRM stage
        lead.status = LeadStatus.ESCALATED
        lead.crm_stage = CRMStage.HOT

        # 3. Update Conversation
        conv_stmt = select(Conversation).where(Conversation.lead_id == lead.id)
        res = await self._db.execute(conv_stmt)
        conv = res.scalar_one_or_none()

        if not conv:
            conv = Conversation(id=uuid.uuid4(), lead_id=lead.id, status=ConversationStatus.ESCALATED)
            self._db.add(conv)
            await self._db.flush()

        conv.status = ConversationStatus.ESCALATED
        conv.ai_auto_respond = False  # Disable AI auto-reply upon escalation
        conv.escalated_at = datetime.now(UTC)

        # 4. Log Event
        self._db.add(ConversationEvent(
            id=uuid.uuid4(),
            conversation_id=conv.id,
            event_type="escalated_hot_lead",
            actor="system",
            details={"reason": reason, "intent_score": intent_score},
        ))

        self._db.add(AuditLog(
            action=AuditAction.CONVERSATION_ESCALATED,
            resource_type="conversation",
            resource_id=str(conv.id),
            details={"lead_id": str(lead.id), "reason": reason, "score": intent_score},
        ))
        await self._db.commit()

        # 5. Send Immediate Operator Notification
        prospect = lead.prospect
        company_name = prospect.company.name if prospect.company else "Unknown Company"
        noti_title = f"🔥 RAYVEN HOT LEAD: {prospect.full_name} ({company_name})"
        noti_body = (
            f"{prospect.full_name} ({prospect.title or 'Executive'} @ {company_name})\n"
            f"Intent Score: {intent_score:.0f}/100\n"
            f"Reason: {reason}\n"
            f"Recommended action: Take over conversation in Dashboard."
        )

        if notification_provider:
            try:
                await notification_provider.notify(NotificationEvent(
                    event_type="hot_lead_escalation",
                    title=noti_title,
                    body=noti_body,
                    lead_id=str(lead.id),
                    conversation_id=str(conv.id),
                    metadata={"intent_score": intent_score, "reason": reason},
                ))
            except Exception as e:
                logger.error(f"Failed to send escalation notification: {e}")

        return {
            "lead_id": str(lead.id),
            "conversation_id": str(conv.id),
            "status": "HOT",
            "ai_auto_respond": False,
            "reason": reason,
        }

    async def take_over_conversation(self, conversation_id: uuid.UUID, operator_id: uuid.UUID) -> Conversation:
        """Human operator takes full manual control of a conversation."""
        conv = await self._db.get(Conversation, conversation_id)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")

        conv.status = ConversationStatus.HUMAN_ENGAGED
        conv.ai_auto_respond = False  # AI must no longer send automatic messages
        conv.human_engaged_at = datetime.now(UTC)
        conv.assigned_to_id = operator_id

        lead = await self._db.get(Lead, conv.lead_id)
        if lead:
            lead.status = LeadStatus.HUMAN_ENGAGED
            lead.is_stopped = True
            lead.stopped_reason = "Human Takeover"

        self._db.add(ConversationEvent(
            id=uuid.uuid4(),
            conversation_id=conv.id,
            event_type="human_takeover",
            actor="human",
            actor_id=operator_id,
            details={"action": "Operator took control of thread"},
        ))

        await self._db.commit()
        await self._db.refresh(conv)
        return conv

    async def return_to_ai(self, conversation_id: uuid.UUID, operator_id: uuid.UUID) -> Conversation:
        """Return conversation to AI automated monitoring/reply mode."""
        conv = await self._db.get(Conversation, conversation_id)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")

        conv.status = ConversationStatus.ACTIVE
        conv.ai_auto_respond = True

        self._db.add(ConversationEvent(
            id=uuid.uuid4(),
            conversation_id=conv.id,
            event_type="returned_to_ai",
            actor="human",
            actor_id=operator_id,
            details={"action": "Operator re-enabled AI automation"},
        ))

        await self._db.commit()
        await self._db.refresh(conv)
        return conv
