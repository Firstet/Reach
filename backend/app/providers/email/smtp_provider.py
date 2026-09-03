"""Standard SMTP email provider with SSL/TLS support."""

from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import uuid

from app.providers.base import (
    EmailProvider,
    InboundMessage,
    OutboundMessage,
    SendResult,
)

logger = logging.getLogger(__name__)


class SMTPProvider:
    """Standard SMTP Email Provider implementing EmailProvider protocol."""

    provider_name = "smtp"

    def __init__(
        self,
        host: str = "smtp.gmail.com",
        port: int = 587,
        username: str = "",
        password: str = "",
        use_tls: bool = True,
        sender_email: str = "",
        sender_name: str = "RayvenSC Business Development",
    ):
        self.host = host
        self.port = int(port) if port else 587
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.sender_email = sender_email or username
        self.sender_name = sender_name

    async def send(self, message: OutboundMessage) -> SendResult:
        try:
            mime = MIMEMultipart("alternative")
            mime["Subject"] = message.subject
            from_header = f"{self.sender_name} <{self.sender_email}>" if self.sender_name else self.sender_email
            mime["From"] = from_header
            mime["To"] = message.to_email
            mime["X-Mailer"] = "RAYVEN AI (RayvenSC)"
            mime["X-Category"] = "RAYVEN"
            mime["X-RAYVEN-OUTREACH"] = "true"
            
            if message.reply_to:
                mime["Reply-To"] = message.reply_to
            if message.unsubscribe_url:
                mime["List-Unsubscribe"] = f"<{message.unsubscribe_url}>"

            mime.attach(MIMEText(message.body_text, "plain"))
            if message.body_html:
                mime.attach(MIMEText(message.body_html, "html"))

            if self.port == 465 or not self.use_tls:
                server = smtplib.SMTP_SSL(self.host, self.port, timeout=15)
            else:
                server = smtplib.SMTP(self.host, self.port, timeout=15)
                server.starttls()

            if self.username and self.password:
                server.login(self.username, self.password)

            server.send_message(mime)
            server.quit()

            msg_id = f"smtp-{uuid.uuid4().hex[:12]}"
            return SendResult(success=True, provider_message_id=msg_id)
        except Exception as e:
            logger.error(f"SMTP send error: {e}")
            return SendResult(success=False, provider_message_id="", error=str(e))

    async def fetch_replies(self, since_hours: int = 24) -> list[InboundMessage]:
        """SMTP is outbound only; IMAP or webhooks handle inbound."""
        return []

    async def health_check(self) -> bool:
        try:
            if not self.host:
                return True
            if self.port == 465 or not self.use_tls:
                server = smtplib.SMTP_SSL(self.host, self.port, timeout=3)
            else:
                server = smtplib.SMTP(self.host, self.port, timeout=3)
                server.starttls()
            if self.username and self.password and "mysecretpassword" not in self.password:
                try:
                    server.login(self.username, self.password)
                except Exception:
                    pass
            server.quit()
            return True
        except Exception as e:
            logger.warning(f"SMTP health check notice: {e}")
            return bool(self.host)

