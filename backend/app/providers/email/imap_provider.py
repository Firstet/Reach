"""Standard IMAP email sync provider with SSL support."""

from __future__ import annotations

import email
import imaplib
import logging
import re
from datetime import UTC, datetime, timedelta
from email.header import decode_header
from typing import Any

from app.providers.base import InboundMessage

logger = logging.getLogger(__name__)


def _decode_mime_words(s: str) -> str:
    """Safely decode MIME encoded header words (e.g. =?UTF-8?B?...?=)."""
    if not s:
        return ""
    try:
        decoded_list = decode_header(s)
        parts = []
        for bytes_or_str, encoding in decoded_list:
            if isinstance(bytes_or_str, bytes):
                try:
                    parts.append(bytes_or_str.decode(encoding or "utf-8", errors="replace"))
                except Exception:
                    parts.append(bytes_or_str.decode("latin-1", errors="replace"))
            else:
                parts.append(str(bytes_or_str))
        return "".join(parts)
    except Exception:
        return str(s)


def _extract_email_address(raw_str: str) -> str:
    """Extract clean email address from header string like 'Name <user@domain.com>'."""
    if not raw_str:
        return ""
    match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", raw_str)
    return match.group(0).lower() if match else raw_str.strip().lower()


class IMAPProvider:
    """IMAP Provider for fetching Inbox, Sent, and Spam folders from email servers."""

    def __init__(
        self,
        host: str = "imap.gmail.com",
        port: int = 993,
        username: str = "",
        password: str = "",
        use_ssl: bool = True,
    ):
        self.host = host or "imap.gmail.com"
        self.port = int(port) if port else 993
        self.username = username
        self.password = password
        self.use_ssl = use_ssl

    def _infer_imap_host(self, smtp_host: str) -> str:
        """Infer IMAP host from SMTP host if generic."""
        if "gmail.com" in smtp_host:
            return "imap.gmail.com"
        elif "zoho" in smtp_host:
            return "imap.zoho.com"
        elif "office365" in smtp_host or "outlook" in smtp_host:
            return "outlook.office365.com"
        elif smtp_host.startswith("smtp."):
            return smtp_host.replace("smtp.", "imap.", 1)
        return smtp_host or "imap.gmail.com"

    def fetch_messages_from_folder(
        self, folder_name: str = "INBOX", since_hours: int | None = None, max_count: int = 500
    ) -> list[InboundMessage]:
        """Synchronously connect via IMAP and extract emails from specified folder."""
        if not self.username or not self.password or "mysecretpassword" in self.password:
            return []

        messages: list[InboundMessage] = []
        mail = None
        try:
            target_host = self._infer_imap_host(self.host)
            if self.use_ssl:
                mail = imaplib.IMAP4_SSL(target_host, self.port, timeout=15)
            else:
                mail = imaplib.IMAP4(target_host, self.port, timeout=15)

            mail.login(self.username, self.password)

            # Try creating RAYVEN category folder on remote server if it doesn't exist
            try:
                mail.create('RAYVEN')
            except Exception:
                pass

            # Select folder
            status, _ = mail.select(f'"{folder_name}"', readonly=True)
            if status != "OK":
                # Try unquoted or fallback folder names
                status, _ = mail.select(folder_name, readonly=True)
                if status != "OK":
                    return []

            # Search messages (SINCE if specified, else ALL for full historical sync)
            if since_hours and since_hours > 0:
                since_date = (datetime.now(UTC) - timedelta(hours=since_hours)).strftime("%d-%b-%Y")
                status, search_data = mail.search(None, f'SINCE "{since_date}"')
                if status != "OK" or not search_data[0]:
                    status, search_data = mail.search(None, "ALL")
            else:
                status, search_data = mail.search(None, "ALL")

            if status == "OK" and search_data[0]:
                msg_ids = search_data[0].split()
                # Take latest max_count messages
                latest_ids = msg_ids[-max_count:]

                for m_id in reversed(latest_ids):
                    try:
                        res, msg_data = mail.fetch(m_id, "(RFC822)")
                        if res != "OK" or not msg_data:
                            continue
                        raw_email = msg_data[0][1]
                        if not isinstance(raw_email, bytes):
                            continue

                        email_message = email.message_from_bytes(raw_email)
                        subject = _decode_mime_words(email_message.get("Subject", ""))
                        from_hdr = _decode_mime_words(email_message.get("From", ""))
                        to_hdr = _decode_mime_words(email_message.get("To", ""))
                        msg_id = email_message.get("Message-ID", f"imap-{uuid.uuid4().hex[:12]}")
                        date_hdr = email_message.get("Date", "")

                        from_email = _extract_email_address(from_hdr)
                        to_email = _extract_email_address(to_hdr)

                        # Parse Body
                        body_text = ""
                        body_html = ""
                        if email_message.is_multipart():
                            for part in email_message.walk():
                                c_type = part.get_content_type()
                                c_disp = str(part.get("Content-Disposition"))
                                if "attachment" in c_disp:
                                    continue
                                if c_type == "text/plain" and not body_text:
                                    payload = part.get_payload(decode=True)
                                    if payload:
                                        body_text = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
                                elif c_type == "text/html" and not body_html:
                                    payload = part.get_payload(decode=True)
                                    if payload:
                                        body_html = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
                        else:
                            c_type = email_message.get_content_type()
                            payload = email_message.get_payload(decode=True)
                            if payload:
                                text_content = payload.decode(email_message.get_content_charset() or "utf-8", errors="replace")
                                if c_type == "text/html":
                                    body_html = text_content
                                else:
                                    body_text = text_content

                        auto_reply = any(
                            kw in subject.lower()
                            for kw in ["out of office", "auto-reply", "automatic reply", "away", "undelivered", "bounce"]
                        )

                        messages.append(
                            InboundMessage(
                                provider_message_id=msg_id.strip("<>"),
                                from_email=from_email,
                                to_email=to_email,
                                subject=subject,
                                body_text=body_text or body_html,
                                body_html=body_html,
                                thread_id=msg_id.strip("<>"),
                                received_at=datetime.now(UTC).isoformat(),
                                is_auto_reply=auto_reply,
                            )
                        )
                    except Exception as err:
                        logger.warning(f"Error parsing IMAP message ID {m_id}: {err}")
        except Exception as e:
            logger.warning(f"IMAP fetch error for folder {folder_name}: {e}")
        finally:
            if mail:
                try:
                    mail.logout()
                except Exception:
                    pass
        return messages
