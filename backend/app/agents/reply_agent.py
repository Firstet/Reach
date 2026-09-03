"""
Reply Agent
Polls inbox for new prospect emails, matches them to active conversations,
classifies intent, stops sequences, and triggers human escalation.
"""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.providers.registry import get_email_provider, get_llm_provider, get_notification_provider
from app.services.conversation import ConversationService

logger = logging.getLogger(__name__)


async def run_reply_agent(db: AsyncSession, since_hours: int = 24) -> dict:
    """Poll email inbox for replies and process each through the Conversation Engine."""
    email_provider = get_email_provider()
    if not email_provider:
        logger.info("No active email provider configured for inbox polling.")
        return {"processed": 0, "reason": "No email provider configured"}

    llm = get_llm_provider()
    notification_provider = get_notification_provider(email_provider)
    service = ConversationService(db)

    try:
        inbound_messages = await email_provider.fetch_replies(since_hours=since_hours)
        processed_count = 0
        escalated_count = 0

        for msg in inbound_messages:
            res = await service.process_inbound_reply(
                from_email=msg.from_email,
                subject=msg.subject,
                body_text=msg.body_text,
                provider_message_id=msg.provider_message_id,
                llm=llm,
                notification_provider=notification_provider,
            )
            if res.get("matched"):
                processed_count += 1
                if res.get("escalated"):
                    escalated_count += 1

        logger.info(f"Reply agent completed: processed {processed_count} replies, escalated {escalated_count}")
        return {"processed": processed_count, "escalated": escalated_count}

    except Exception as e:
        logger.error(f"Reply agent execution failed: {e}", exc_info=True)
        return {"processed": 0, "error": str(e)}
