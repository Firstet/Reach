"""
Provider abstraction interfaces.
All providers implement typed Protocol classes so they can be swapped without
touching business logic. Concrete implementations live in subdirectories.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


# ── Common Data Classes ───────────────────────────────────────────────────────

@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    source: str = ""


@dataclass
class EmailResult:
    email: str
    confidence: float  # 0.0–1.0
    source: str
    first_name: str = ""
    last_name: str = ""


@dataclass
class VerificationResult:
    email: str
    is_valid: bool
    is_disposable: bool
    is_role_account: bool
    status: str  # valid | invalid | risky | unknown
    confidence: float


@dataclass
class OutboundMessage:
    to_email: str
    from_email: str
    subject: str
    body_html: str
    body_text: str
    reply_to: str = ""
    thread_id: str = ""
    unsubscribe_url: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass
class SendResult:
    success: bool
    provider_message_id: str
    error: str = ""


@dataclass
class InboundMessage:
    provider_message_id: str
    from_email: str
    to_email: str
    subject: str
    body_text: str
    body_html: str
    thread_id: str
    received_at: str  # ISO8601
    is_auto_reply: bool = False
    metadata: dict = field(default_factory=dict)


@dataclass
class LinkedInProfile:
    url: str
    full_name: str
    headline: str
    location: str
    about: str = ""
    current_company: str = ""
    current_title: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass
class NotificationEvent:
    event_type: str
    title: str
    body: str
    lead_id: str = ""
    conversation_id: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass
class Chunk:
    id: str
    content: str
    embedding: list[float]
    metadata: dict = field(default_factory=dict)


@dataclass
class LLMMessage:
    role: str  # system | user | assistant
    content: str


# ── Provider Protocols ────────────────────────────────────────────────────────

@runtime_checkable
class LLMProvider(Protocol):
    """Pluggable LLM provider (OpenAI, Anthropic, Gemini, Ollama, ...)."""

    provider_name: str

    async def complete(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs: Any,
    ) -> str: ...

    async def embed(self, text: str) -> list[float]: ...

    async def health_check(self) -> bool: ...


@runtime_checkable
class SearchProvider(Protocol):
    """Pluggable web search provider."""

    provider_name: str

    async def search(
        self,
        query: str,
        num_results: int = 10,
        **kwargs: Any,
    ) -> list[SearchResult]: ...

    async def health_check(self) -> bool: ...


@runtime_checkable
class LeadDataProvider(Protocol):
    """Pluggable provider for company lead and decision-maker data discovery."""

    provider_name: str

    async def search_company_leads(
        self,
        company_name: str,
        domain: str,
    ) -> list[dict]: ...

    async def health_check(self) -> bool: ...


@runtime_checkable
class EmailEnrichmentProvider(Protocol):
    """Pluggable email finder provider."""

    provider_name: str

    async def find_email(
        self,
        first_name: str,
        last_name: str,
        domain: str,
    ) -> EmailResult | None: ...

    async def health_check(self) -> bool: ...


@runtime_checkable
class EmailVerificationProvider(Protocol):
    """Pluggable email verification provider."""

    provider_name: str

    async def verify_email(self, email: str) -> VerificationResult: ...

    async def health_check(self) -> bool: ...


@runtime_checkable
class EnrichmentProvider(Protocol):
    """Pluggable unified email enrichment & verification provider."""

    provider_name: str

    async def find_email(
        self,
        first_name: str,
        last_name: str,
        domain: str,
    ) -> EmailResult | None: ...

    async def verify_email(self, email: str) -> VerificationResult: ...

    async def health_check(self) -> bool: ...



@runtime_checkable
class EmailProvider(Protocol):
    """Pluggable email sending & inbox polling provider."""

    provider_name: str

    async def send(self, message: OutboundMessage) -> SendResult: ...

    async def fetch_replies(
        self, since_hours: int = 24
    ) -> list[InboundMessage]: ...

    async def health_check(self) -> bool: ...


@runtime_checkable
class LinkedInProvider(Protocol):
    """
    Optional LinkedIn browser automation provider.
    All methods are optional — the rest of the system must work without this.
    """

    provider_name: str
    is_enabled: bool

    async def search_people(
        self, query: str, filters: dict | None = None
    ) -> list[LinkedInProfile]: ...

    async def get_profile(self, url: str) -> LinkedInProfile | None: ...

    async def health_check(self) -> bool: ...


@runtime_checkable
class NotificationProvider(Protocol):
    """Pluggable human notification provider (email, Slack, webhook)."""

    provider_name: str

    async def notify(self, event: NotificationEvent) -> bool: ...

    async def health_check(self) -> bool: ...


@runtime_checkable
class VectorStoreProvider(Protocol):
    """Pluggable vector store (pgvector, Pinecone, Qdrant, ...)."""

    provider_name: str

    async def upsert(self, chunks: list[Chunk]) -> None: ...

    async def search(
        self,
        query_embedding: list[float],
        k: int = 5,
        threshold: float = 0.75,
    ) -> list[Chunk]: ...

    async def delete(self, chunk_ids: list[str]) -> None: ...

    async def health_check(self) -> bool: ...
