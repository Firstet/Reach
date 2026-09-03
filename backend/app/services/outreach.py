"""
Outreach Execution Service
Handles message sending (via Gmail / EmailProvider), test mode simulation,
send-window validation, daily limit enforcement, threading, and reply-triggered sequence stops.
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
    Campaign,
    CampaignStatus,
    Lead,
    LeadStatus,
    Message,
    MessageDirection,
    MessageStatus,
    Prospect,
)
from app.providers.base import EmailProvider, OutboundMessage
from app.services.safety import SafetyService

logger = logging.getLogger(__name__)


class OutreachService:
    """Manages email sending and sequence stopping logic."""

    def __init__(self, session: AsyncSession):
        self._db = session
        self._safety = SafetyService(session)

    async def send_lead_message(
        self,
        lead_id: uuid.UUID,
        email_provider: EmailProvider | None = None,
        override_message_id: uuid.UUID | None = None,
    ) -> dict:
        """
        Execute send for a lead's pending draft message.
        Enforces safety checks, test mode, daily limits, and send windows.
        """
        from sqlalchemy.orm import selectinload
        lead_stmt = (
            select(Lead)
            .where(Lead.id == lead_id)
            .options(
                selectinload(Lead.prospect).selectinload(Prospect.company),
                selectinload(Lead.campaign),
            )
        )
        lead_res = await self._db.execute(lead_stmt)
        lead = lead_res.scalar_one_or_none()

        if not lead or not lead.prospect:
            return {"success": False, "reason": "Lead or prospect not found"}

        # Perform full safety check
        can_send, reason = await self._safety.can_send_to_lead(lead)
        if not can_send:
            logger.warning(f"Cannot send to lead {lead_id}: {reason}")
            return {"success": False, "reason": reason}

        campaign = lead.campaign
        prospect = lead.prospect

        # Find pending draft message
        stmt = select(Message).where(
            Message.lead_id == lead.id,
            Message.direction == MessageDirection.OUTBOUND,
            Message.status == MessageStatus.DRAFT,
        )
        if override_message_id:
            stmt = stmt.where(Message.id == override_message_id)

        stmt = stmt.order_by(Message.created_at.desc())
        res = await self._db.execute(stmt)
        msg = res.scalar_one_or_none()

        if not msg:
            return {"success": False, "reason": "No pending draft message found for lead"}

        # Unsubscribe link handling if enabled
        from_email = (email_provider.sender_email if hasattr(email_provider, 'sender_email') else None) or "outreach@rayvensc.com"
        unsubscribe_url = f"{campaign.description or ''}/api/v1/suppression/unsubscribe?p={prospect.id}"

        # Append configured Email Signature
        from app.core.config import get_settings
        settings = get_settings()

        sig_text = settings.email_signature_text or "\n---\nWarm regards,\nRayven Strategic Communications\nAbuja, Nigeria | hello@rayvensc.com"
        sig_html = settings.email_signature_html or "<br><br><hr><p><strong>Warm regards,</strong><br>Rayven Strategic Communications<br>Abuja, Nigeria | hello@rayvensc.com</p>"

        final_text = msg.body
        if sig_text and sig_text not in final_text:
            final_text = f"{final_text}\n\n{sig_text}"

        final_html = f"<p>{msg.body.replace(chr(10), '<br>')}</p>"
        if sig_html and sig_html not in final_html:
            final_html = f"{final_html}<br>{sig_html}"

        outbound = OutboundMessage(
            to_email=prospect.email,
            from_email=from_email,
            subject=msg.subject or f"Strategic Communications — {prospect.company.name if prospect.company else ''}",
            body_text=final_text,
            body_html=final_html,
            unsubscribe_url=unsubscribe_url,
        )

        # CHECK TEST MODE OR UNCONFIGURED SMTP PROVIDER
        is_simulated = campaign.test_mode or lead.is_test or not email_provider or getattr(email_provider, 'name', '') == 'disabled'

        if is_simulated:
            logger.info(f"[SIMULATION MODE] Executed email send to {prospect.email} — Subject: '{outbound.subject}'")
            msg.status = MessageStatus.SENT
            msg.sent_at = datetime.now(UTC)
            msg.provider_message_id = f"simulated-{uuid.uuid4()}"
            msg.from_email = from_email
            msg.to_email = prospect.email

            lead.outreach_count += 1
            lead.last_contacted_at = datetime.now(UTC)
            lead.status = LeadStatus.OUTREACH_SENT
            campaign.daily_sends_today += 1

            self._db.add(AuditLog(
                action=AuditAction.MESSAGE_SENT,
                resource_type="message",
                resource_id=str(msg.id),
                details={"to": prospect.email, "test_mode": True, "subject": msg.subject},
            ))
            await self._db.commit()
            return {"success": True, "simulated": True, "message_id": str(msg.id)}

        # REAL SEND MODE

        try:
            result = await email_provider.send(outbound)
            if result.success:
                msg.status = MessageStatus.SENT
                msg.sent_at = datetime.now(UTC)
                msg.provider_message_id = result.provider_message_id
                msg.from_email = from_email
                msg.to_email = prospect.email

                lead.outreach_count += 1
                lead.last_contacted_at = datetime.now(UTC)
                lead.status = LeadStatus.OUTREACH_SENT
                campaign.daily_sends_today += 1

                self._db.add(AuditLog(
                    action=AuditAction.MESSAGE_SENT,
                    resource_type="message",
                    resource_id=str(msg.id),
                    details={"to": prospect.email, "provider_msg_id": result.provider_message_id},
                ))
                await self._db.commit()
                return {"success": True, "message_id": str(msg.id), "provider_msg_id": result.provider_message_id}
            else:
                msg.status = MessageStatus.FAILED
                await self._db.commit()
                return {"success": False, "reason": f"Email provider error: {result.error}"}

        except Exception as e:
            logger.error(f"Send failed for lead {lead_id}: {e}", exc_info=True)
            msg.status = MessageStatus.FAILED
            await self._db.commit()
            return {"success": False, "reason": str(e)}

    async def stop_automated_sequence(self, lead_id: uuid.UUID, reason: str) -> None:
        """
        CRITICAL RULE: Immediately stop automated follow-ups for a lead.
        Called on reply, escalation, unsubscribe, or human takeover.
        """
        lead = await self._db.get(Lead, lead_id)
        if not lead:
            return

        lead.is_stopped = True
        lead.stopped_reason = reason
        if lead.status not in (LeadStatus.CONVERTED, LeadStatus.UNSUBSCRIBED):
            lead.status = LeadStatus.REPLIED if "reply" in reason else LeadStatus.PAUSED

        logger.info(f"STOPPED automated sequence for Lead {lead_id}. Reason: {reason}")
        await self._db.commit()
