"""Gmail OAuth2 email provider."""

from __future__ import annotations

import base64
import email as email_lib
import logging
from datetime import UTC, datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.providers.base import (
    EmailProvider,
    InboundMessage,
    OutboundMessage,
    SendResult,
)

logger = logging.getLogger(__name__)
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


class GmailProvider:
    """Gmail OAuth2 email provider implementing EmailProvider protocol."""

    provider_name = "gmail"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        sender_email: str,
    ):
        self._sender_email = sender_email
        self._creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            client_id=client_id,
            client_secret=client_secret,
            token_uri="https://oauth2.googleapis.com/token",
            scopes=SCOPES,
        )

    def _get_service(self):
        if not self._creds.valid:
            self._creds.refresh(Request())
        return build("gmail", "v1", credentials=self._creds)

    def _build_message(self, msg: OutboundMessage) -> dict:
        mime = MIMEMultipart("alternative")
        mime["Subject"] = msg.subject
        mime["From"] = self._sender_email
        mime["To"] = msg.to_email
        if msg.reply_to:
            mime["Reply-To"] = msg.reply_to
        if msg.unsubscribe_url:
            mime["List-Unsubscribe"] = f"<{msg.unsubscribe_url}>"
        mime.attach(MIMEText(msg.body_text, "plain"))
        mime.attach(MIMEText(msg.body_html, "html"))
        raw = base64.urlsafe_b64encode(mime.as_bytes()).decode()
        body: dict = {"raw": raw}
        if msg.thread_id:
            body["threadId"] = msg.thread_id
        return body

    async def send(self, message: OutboundMessage) -> SendResult:
        try:
            service = self._get_service()
            result = (
                service.users()
                .messages()
                .send(userId="me", body=self._build_message(message))
                .execute()
            )
            return SendResult(success=True, provider_message_id=result["id"])
        except HttpError as e:
            logger.error(f"Gmail send error: {e}")
            return SendResult(success=False, provider_message_id="", error=str(e))

    async def fetch_replies(self, since_hours: int = 24) -> list[InboundMessage]:
        try:
            service = self._get_service()
            since_ts = int(
                (datetime.now(UTC) - timedelta(hours=since_hours)).timestamp()
            )
            query = f"is:inbox after:{since_ts}"
            result = (
                service.users()
                .messages()
                .list(userId="me", q=query, maxResults=50)
                .execute()
            )
            messages = []
            for msg_ref in result.get("messages", []):
                msg = (
                    service.users()
                    .messages()
                    .get(userId="me", id=msg_ref["id"], format="full")
                    .execute()
                )
                parsed = self._parse_message(msg)
                if parsed:
                    messages.append(parsed)
            return messages
        except HttpError as e:
            logger.error(f"Gmail fetch error: {e}")
            return []

    def _parse_message(self, msg: dict) -> InboundMessage | None:
        headers = {
            h["name"].lower(): h["value"]
            for h in msg.get("payload", {}).get("headers", [])
        }
        from_email = headers.get("from", "")
        to_email = headers.get("to", "")
        subject = headers.get("subject", "")
        thread_id = msg.get("threadId", "")
        internal_date = int(msg.get("internalDate", 0)) // 1000
        received_at = datetime.fromtimestamp(internal_date, tz=UTC).isoformat()

        body_text = ""
        body_html = ""

        def extract_body(payload):
            nonlocal body_text, body_html
            mime_type = payload.get("mimeType", "")
            if mime_type == "text/plain":
                data = payload.get("body", {}).get("data", "")
                body_text = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
            elif mime_type == "text/html":
                data = payload.get("body", {}).get("data", "")
                body_html = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
            for part in payload.get("parts", []):
                extract_body(part)

        extract_body(msg.get("payload", {}))

        auto_reply = any(
            kw in subject.lower()
            for kw in ["out of office", "auto-reply", "automatic reply", "away"]
        )

        return InboundMessage(
            provider_message_id=msg["id"],
            from_email=from_email,
            to_email=to_email,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            thread_id=thread_id,
            received_at=received_at,
            is_auto_reply=auto_reply,
        )

    async def health_check(self) -> bool:
        try:
            service = self._get_service()
            service.users().getProfile(userId="me").execute()
            return True
        except Exception as e:
            logger.error(f"Gmail health check failed: {e}")
            return False
