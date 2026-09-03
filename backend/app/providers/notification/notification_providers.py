"""Notification providers: email and Slack."""

from __future__ import annotations

import logging

import httpx

from app.providers.base import NotificationEvent, NotificationProvider

logger = logging.getLogger(__name__)


class SlackNotificationProvider:
    """Posts notifications to a Slack webhook."""

    provider_name = "slack"

    def __init__(self, webhook_url: str, channel: str = "#bd-alerts"):
        self._webhook_url = webhook_url
        self._channel = channel
        self._client = httpx.AsyncClient(timeout=10.0)

    async def notify(self, event: NotificationEvent) -> bool:
        try:
            payload = {
                "channel": self._channel,
                "blocks": [
                    {
                        "type": "header",
                        "text": {"type": "plain_text", "text": f"🔔 {event.title}"},
                    },
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": event.body},
                    },
                ],
            }
            if event.lead_id:
                payload["blocks"].append({
                    "type": "context",
                    "elements": [
                        {"type": "mrkdwn", "text": f"Lead: `{event.lead_id}` · Type: `{event.event_type}`"}
                    ],
                })
            resp = await self._client.post(self._webhook_url, json=payload)
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"Slack notification failed: {e}")
            return False

    async def health_check(self) -> bool:
        return bool(self._webhook_url)


class EmailNotificationProvider:
    """Sends escalation notifications via the configured email provider."""

    provider_name = "email_notification"

    def __init__(self, escalation_email: str, email_provider):
        self._escalation_email = escalation_email
        self._email_provider = email_provider

    async def notify(self, event: NotificationEvent) -> bool:
        from app.providers.base import OutboundMessage

        msg = OutboundMessage(
            to_email=self._escalation_email,
            from_email=self._escalation_email,
            subject=f"[Reach] {event.title}",
            body_text=event.body,
            body_html=f"<p>{event.body.replace(chr(10), '<br>')}</p>",
        )
        try:
            result = await self._email_provider.send(msg)
            return result.success
        except Exception as e:
            logger.error(f"Email notification failed: {e}")
            return False

    async def health_check(self) -> bool:
        return True


class WebhookNotificationProvider:
    """Posts notifications to a generic webhook endpoint."""

    provider_name = "webhook"

    def __init__(self, webhook_url: str, secret: str = ""):
        self._webhook_url = webhook_url
        self._secret = secret
        self._client = httpx.AsyncClient(timeout=10.0)

    async def notify(self, event: NotificationEvent) -> bool:
        try:
            headers = {}
            if self._secret:
                headers["X-Reach-Signature"] = self._secret
            resp = await self._client.post(
                self._webhook_url,
                json={
                    "event_type": event.event_type,
                    "title": event.title,
                    "body": event.body,
                    "lead_id": event.lead_id,
                    "conversation_id": event.conversation_id,
                    "metadata": event.metadata,
                },
                headers=headers,
            )
            return resp.status_code < 400
        except Exception as e:
            logger.error(f"Webhook notification failed: {e}")
            return False

    async def health_check(self) -> bool:
        return bool(self._webhook_url)
