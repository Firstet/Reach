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


async def run_reply_agent(db: AsyncSession, since_hours: int = 48) -> dict:
    """Poll email inbox and IMAP folders for replies and process each through the Conversation Engine."""
    from app.core.config import get_settings
    from app.providers.email.imap_provider import IMAPProvider
    settings = get_settings()

    email_provider = get_email_provider()
    llm = get_llm_provider()
    notification_provider = get_notification_provider(email_provider)
    service = ConversationService(db)

    processed_count = 0
    escalated_count = 0

    try:
        # 1. Fetch via primary email provider if available
        if email_provider:
            inbound_messages = await email_provider.fetch_replies(since_hours=since_hours)
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

        # 2. Synchronize via IMAP if SMTP credentials configured
        if settings.smtp_username and settings.smtp_password and "mysecretpassword" not in settings.smtp_password:
            imap_prov = IMAPProvider(
                host=settings.smtp_host,
                port=993,
                username=settings.smtp_username,
                password=settings.smtp_password,
                use_ssl=True,
            )
            # Fetch INBOX & Spam
            for folder in ["INBOX", "Spam", "Junk"]:
                imap_msgs = imap_prov.fetch_messages_from_folder(folder_name=folder, since_hours=since_hours)
                for msg in imap_msgs:
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

        logger.info(f"Reply agent completed: processed {processed_count} replies, escalated {escalated_count}")
        return {"processed": processed_count, "escalated": escalated_count}

    except Exception as e:
        logger.error(f"Reply agent execution failed: {e}", exc_info=True)
        return {"processed": processed_count, "error": str(e)}
