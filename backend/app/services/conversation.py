"""
Conversation Engine & Reply Intelligence Service (Phase 3 Enhanced)
State machine management, 13 intent classification, buying signal detection,
routine Q&A auto-answering with KB citations, and human takeover escalations.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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
    MessageStatus,
    Notification,
    NotificationStatus,
    Prospect,
    ReplyIntent,
)
from app.providers.base import LLMMessage, LLMProvider, NotificationProvider
from app.services.auto_answer import AutoAnswerEngine
from app.services.handoff import HumanHandoffService
from app.services.intent_detector import IntentDetector
from app.services.outreach import OutreachService
from app.services.safety import SafetyService

logger = logging.getLogger(__name__)


class ConversationService:
    """Manages conversation state machine, intent analysis, auto-answering, and escalations."""

    def __init__(self, session: AsyncSession):
        self._db = session
        self._outreach = OutreachService(session)
        self._safety = SafetyService(session)
        self._auto_answer = AutoAnswerEngine(session)
        self._intent_detector = IntentDetector()
        self._handoff = HumanHandoffService(session)

    async def process_inbound_reply(
        self,
        from_email: str,
        subject: str,
        body_text: str,
        provider_message_id: str = "",
        llm: LLMProvider | None = None,
        notification_provider: NotificationProvider | None = None,
    ) -> dict:
        """
        Process incoming prospect reply:
        1. Match prospect & lead
        2. IMMEDIATELY STOP automated follow-up sequence
        3. Analyze Intent & Buying Signals
        4. Decide: Auto-Answer vs Mandatory Human Escalation
        """
        clean_email = from_email.lower().strip()

        # 1. Match Prospect
        stmt = select(Prospect).where(Prospect.email == clean_email)
        res = await self._db.execute(stmt)
        prospect = res.scalar_one_or_none()

        if not prospect:
            from app.models import Company
            # Auto-create Prospect for historical email sync
            company_name = clean_email.split("@")[-1].split(".")[0].capitalize()
            comp_stmt = select(Company).where(Company.domain == clean_email.split("@")[-1])
            comp_res = await self._db.execute(comp_stmt)
            company = comp_res.scalar_one_or_none()
            if not company:
                company = Company(id=uuid.uuid4(), name=company_name, domain=clean_email.split("@")[-1])
                self._db.add(company)
                await self._db.flush()

            name_parts = clean_email.split("@")[0].replace(".", " ").replace("_", " ").title().split()
            first_name = name_parts[0] if name_parts else "Executive"
            last_name = name_parts[-1] if len(name_parts) > 1 else "Contact"

            prospect = Prospect(
                id=uuid.uuid4(),
                company_id=company.id,
                email=clean_email,
                first_name=first_name,
                last_name=last_name,
                title="Executive Contact",
            )
            self._db.add(prospect)
            await self._db.flush()

        # Find or create active lead
        lead_stmt = select(Lead).where(Lead.prospect_id == prospect.id).order_by(Lead.updated_at.desc())
        lead_res = await self._db.execute(lead_stmt)
        lead = lead_res.scalar_one_or_none()

        if not lead:
            from app.models import Campaign
            camp_stmt = select(Campaign).limit(1)
            camp_res = await self._db.execute(camp_stmt)
            camp = camp_res.scalar_one_or_none()

            lead = Lead(
                id=uuid.uuid4(),
                campaign_id=camp.id if camp else None,
                prospect_id=prospect.id,
                status=LeadStatus.DISCOVERED,
                crm_stage=CRMStage.ENGAGED,
            )
            self._db.add(lead)
            await self._db.flush()

        # 2. IMMEDIATELY STOP AUTOMATED OUTREACH SEQUENCE
        await self._outreach.stop_automated_sequence(lead.id, reason=f"Inbound reply received from {clean_email}")

        lead.reply_count += 1
        lead.last_replied_at = datetime.now(UTC)

        # Create or get Conversation
        conv_stmt = select(Conversation).where(Conversation.lead_id == lead.id)
        conv_res = await self._db.execute(conv_stmt)
        conv = conv_res.scalar_one_or_none()

        if not conv:
            conv = Conversation(id=uuid.uuid4(), lead_id=lead.id, status=ConversationStatus.ACTIVE, subject=subject)
            self._db.add(conv)
            await self._db.flush()

        # Save Inbound Message
        inbound_msg = Message(
            id=uuid.uuid4(),
            lead_id=lead.id,
            conversation_id=conv.id,
            direction=MessageDirection.INBOUND,
            status=MessageStatus.DELIVERED,
            subject=subject,
            body=body_text,
            from_email=clean_email,
            to_email="hello@rayvensc.com",
            provider_message_id=provider_message_id,
            is_auto_generated=False,
            sent_at=datetime.now(UTC),
        )
        self._db.add(inbound_msg)

        # 3. Analyze Buying Signals & Intent
        intent_analysis = await self._intent_detector.analyze_with_llm(body_text, llm) if llm else self._intent_detector.analyze_reply(body_text)
        conv.last_reply_intent = intent_analysis.intent

        # Update CRM Stage
        if intent_analysis.intent == ReplyIntent.UNSUBSCRIBE:
            conv.status = ConversationStatus.CLOSED
            lead.status = LeadStatus.UNSUBSCRIBED
            lead.crm_stage = CRMStage.DO_NOT_CONTACT
            await self._safety.unsubscribe_prospect(str(prospect.id), reason="Reply unsubscribe request")
            await self._db.commit()
            return {"matched": True, "intent": "UNSUBSCRIBE", "action": "unsubscribed"}

        elif intent_analysis.intent == ReplyIntent.NOT_INTERESTED:
            conv.status = ConversationStatus.CLOSED
            lead.status = LeadStatus.NOT_INTERESTED
            lead.crm_stage = CRMStage.LOST
            await self._db.commit()
            return {"matched": True, "intent": "NOT_INTERESTED", "action": "closed"}

        # 4. Check if High Intent or Meeting Request
        if intent_analysis.is_high_intent or intent_analysis.intent in (ReplyIntent.HIGH_INTENT, ReplyIntent.MEETING_REQUEST, ReplyIntent.PRICING, ReplyIntent.NEGOTIATION):
            # MANDATORY HUMAN ESCALATION & TAKEOVER
            escalate_res = await self._handoff.escalate_hot_lead(
                lead_id=lead.id,
                reason=f"High Intent Detected ({intent_analysis.intent.value}): {intent_analysis.summary}",
                intent_score=intent_analysis.intent_score,
                notification_provider=notification_provider,
            )
            lead.crm_stage = CRMStage.HOT if intent_analysis.intent != ReplyIntent.MEETING_REQUEST else CRMStage.MEETING
            await self._db.commit()
            return {"matched": True, "intent": intent_analysis.intent.value, "escalated": True, "hot": True, "handoff": escalate_res}

        # 5. Evaluate Auto-Answer vs Mandatory Escalation for Routine Questions
        decision = await self._auto_answer.evaluate_and_answer(body_text, llm)

        if decision.can_auto_answer and conv.ai_auto_respond and not lead.is_stopped:
            # Auto-respond with KB cited answer
            auto_reply_msg = Message(
                id=uuid.uuid4(),
                lead_id=lead.id,
                conversation_id=conv.id,
                direction=MessageDirection.OUTBOUND,
                status=MessageStatus.SENT,
                subject=f"Re: {subject}",
                body=decision.suggested_answer,
                from_email="hello@rayvensc.com",
                to_email=clean_email,
                is_auto_generated=True,
                generation_metadata={"citations": decision.citations, "confidence": decision.confidence},
                sent_at=datetime.now(UTC),
            )
            self._db.add(auto_reply_msg)
            conv.status = ConversationStatus.AUTO_RESPONDED
            lead.status = LeadStatus.AUTO_RESPONDED
            lead.crm_stage = CRMStage.ENGAGED

            self._db.add(ConversationEvent(
                id=uuid.uuid4(),
                conversation_id=conv.id,
                event_type="auto_answer_sent",
                actor="agent",
                details={"confidence": decision.confidence, "citations": decision.citations},
            ))
            await self._db.commit()
            return {"matched": True, "intent": intent_analysis.intent.value, "auto_answered": True, "answer": decision.suggested_answer}

        else:
            # Escalate to Human Operator
            escalate_res = await self._handoff.escalate_hot_lead(
                lead_id=lead.id,
                reason=decision.reason,
                intent_score=intent_analysis.intent_score,
                notification_provider=notification_provider,
            )
            lead.crm_stage = CRMStage.ENGAGED
            await self._db.commit()
            return {"matched": True, "intent": intent_analysis.intent.value, "escalated": True, "reason": decision.reason}
