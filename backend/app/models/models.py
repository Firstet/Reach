"""
SQLAlchemy ORM models for the Reach platform.
All tables use UUID primary keys and include created_at / updated_at timestamps.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


# ── Enums ─────────────────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


class LeadStatus(str, enum.Enum):
    NEW = "new"
    DISCOVERED = "discovered"
    ENRICHED = "enriched"
    RESEARCHED = "researched"
    SCORED = "scored"
    QUALIFIED = "qualified"
    OUTREACH_PENDING = "outreach_pending"
    OUTREACH_SENT = "outreach_sent"
    FOLLOW_UP = "follow_up"
    REPLIED = "replied"
    INTENT_CLASSIFIED = "intent_classified"
    AUTO_RESPONDED = "auto_responded"
    ESCALATED = "escalated"
    HUMAN_ENGAGED = "human_engaged"
    CONVERTED = "converted"
    NOT_INTERESTED = "not_interested"
    UNSUBSCRIBED = "unsubscribed"
    PAUSED = "paused"
    LOST = "lost"
    ARCHIVED = "archived"


class CampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    CONFIGURED = "configured"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ConversationStatus(str, enum.Enum):
    INACTIVE = "inactive"
    ACTIVE = "active"
    AWAITING_REPLY = "awaiting_reply"
    REPLY_RECEIVED = "reply_received"
    CLASSIFYING = "classifying"
    AUTO_RESPONDED = "auto_responded"
    ESCALATED = "escalated"
    HUMAN_ENGAGED = "human_engaged"
    CLOSED = "closed"


class MessageDirection(str, enum.Enum):
    OUTBOUND = "outbound"
    INBOUND = "inbound"


class MessageStatus(str, enum.Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENT = "sent"
    DELIVERED = "delivered"
    BOUNCED = "bounced"
    FAILED = "failed"


class CRMStage(str, enum.Enum):
    DISCOVERED = "discovered"
    QUALIFIED = "qualified"
    CONTACTED = "contacted"
    ENGAGED = "engaged"
    INTERESTED = "interested"
    HOT = "hot"
    MEETING = "meeting"
    PROPOSAL = "proposal"
    WON = "won"
    LOST = "lost"
    NURTURE = "nurture"
    DO_NOT_CONTACT = "do_not_contact"


class ReplyIntent(str, enum.Enum):
    NOT_INTERESTED = "not_interested"
    POLITE_RESPONSE = "polite_response"
    QUESTION = "question"
    CURIOUS = "curious"
    INTERESTED = "interested"
    HIGH_INTENT = "high_intent"
    MEETING_REQUEST = "meeting_request"
    PRICING = "pricing"
    NEGOTIATION = "negotiation"
    COMPLAINT = "complaint"
    UNSUBSCRIBE = "unsubscribe"
    DO_NOT_CONTACT = "do_not_contact"
    UNKNOWN = "unknown"
    ROUTINE_QUESTION = "routine_question"
    OUT_OF_OFFICE = "out_of_office"
    REFERRAL = "referral"
    AMBIGUOUS = "ambiguous"


class AgentStatusEnum(str, enum.Enum):
    IDLE = "idle"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class NotificationStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    READ = "read"
    FAILED = "failed"


class AuditAction(str, enum.Enum):
    # Auth
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    # Lead
    LEAD_CREATED = "lead_created"
    LEAD_UPDATED = "lead_updated"
    LEAD_ENRICHED = "lead_enriched"
    LEAD_SCORED = "lead_scored"
    LEAD_ESCALATED = "lead_escalated"
    # Campaign
    CAMPAIGN_CREATED = "campaign_created"
    CAMPAIGN_STARTED = "campaign_started"
    CAMPAIGN_PAUSED = "campaign_paused"
    # Message
    MESSAGE_SENT = "message_sent"
    MESSAGE_RECEIVED = "message_received"
    MESSAGE_BOUNCED = "message_bounced"
    # Conversation
    CONVERSATION_ESCALATED = "conversation_escalated"
    HUMAN_REPLIED = "human_replied"
    AUTOMATION_RESUMED = "automation_resumed"
    # Config
    CONFIG_UPDATED = "config_updated"
    # Agent
    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"
    AGENT_FAILED = "agent_failed"
    # Knowledge
    KNOWLEDGE_INGESTED = "knowledge_ingested"
    KNOWLEDGE_DELETED = "knowledge_deleted"


# ── Mixin ─────────────────────────────────────────────────────────────────────

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# ── Models ────────────────────────────────────────────────────────────────────

class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), nullable=False, default=UserRole.OPERATOR
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    audit_logs: Mapped[list[AuditLog]] = relationship("AuditLog", back_populates="user")
    conversations: Mapped[list[Conversation]] = relationship(
        "Conversation", back_populates="assigned_to"
    )


class Company(Base, TimestampMixin):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    website: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sub_industry: Mapped[str | None] = mapped_column(String(255), nullable=True)
    size: Mapped[str | None] = mapped_column(String(100), nullable=True)  # e.g. "51-200"
    employee_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    twitter_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    technologies: Mapped[list | None] = mapped_column(JSON, nullable=True)
    funding_stage: Mapped[str | None] = mapped_column(String(100), nullable=True)
    annual_revenue: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    enrichment_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    research_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    prospects: Mapped[list[Prospect]] = relationship("Prospect", back_populates="company")

    __table_args__ = (
        UniqueConstraint("domain", name="uq_company_domain"),
    )


class Prospect(Base, TimestampMixin):
    __tablename__ = "prospects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True
    )
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    email_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    seniority: Mapped[str | None] = mapped_column(String(100), nullable=True)
    department: Mapped[str | None] = mapped_column(String(255), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    twitter_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(100), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    enrichment_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    research_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_unsubscribed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    unsubscribed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    company: Mapped[Company | None] = relationship("Company", back_populates="prospects")
    leads: Mapped[list[Lead]] = relationship("Lead", back_populates="prospect")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


class Campaign(Base, TimestampMixin):
    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[CampaignStatus] = mapped_column(
        Enum(CampaignStatus), nullable=False, default=CampaignStatus.DRAFT
    )
    target_industry: Mapped[str | None] = mapped_column(String(255), nullable=True)
    target_company_size: Mapped[str | None] = mapped_column(String(100), nullable=True)
    target_seniority: Mapped[str | None] = mapped_column(String(100), nullable=True)
    target_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    daily_send_limit: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    send_window_start: Mapped[int] = mapped_column(Integer, default=9, nullable=False)
    send_window_end: Mapped[int] = mapped_column(Integer, default=17, nullable=False)
    max_follow_ups: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    follow_up_delay_hours: Mapped[int] = mapped_column(Integer, default=72, nullable=False)
    value_proposition: Mapped[str | None] = mapped_column(Text, nullable=True)
    personalization_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    test_mode: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    approval_mode: Mapped[str] = mapped_column(String(20), default="auto", nullable=False)  # auto | manual
    min_score_threshold: Mapped[float] = mapped_column(Float, default=40.0, nullable=False)
    discovery_query: Mapped[str | None] = mapped_column(Text, nullable=True)
    scoring_weights: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    tracking_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    require_email_verification: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    daily_sends_today: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_tick_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paused_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    steps: Mapped[list[CampaignStep]] = relationship(
        "CampaignStep", back_populates="campaign", order_by="CampaignStep.step_order"
    )
    leads: Mapped[list[Lead]] = relationship("Lead", back_populates="campaign")


class CampaignStep(Base, TimestampMixin):
    __tablename__ = "campaign_steps"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False
    )
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    step_type: Mapped[str] = mapped_column(String(50), nullable=False)  # email | wait | task
    subject_template: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    body_template: Mapped[str | None] = mapped_column(Text, nullable=True)
    wait_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    campaign: Mapped[Campaign] = relationship("Campaign", back_populates="steps")


class Lead(Base, TimestampMixin):
    """
    The central engagement unit — a Prospect enrolled in a Campaign.
    All agent state, messages, scores, and conversation threads hang off a Lead.
    """
    __tablename__ = "leads"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prospect_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("prospects.id", ondelete="RESTRICT"), nullable=False
    )
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[LeadStatus] = mapped_column(
        Enum(LeadStatus), nullable=False, default=LeadStatus.NEW, index=True
    )
    current_step: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    next_action_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_contacted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_replied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    outreach_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reply_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_stopped: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    stopped_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    assigned_to_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_test: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    discovery_source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    crm_stage: Mapped[CRMStage] = mapped_column(
        Enum(CRMStage), nullable=False, default=CRMStage.DISCOVERED, index=True
    )

    prospect: Mapped[Prospect] = relationship("Prospect", back_populates="leads")
    campaign: Mapped[Campaign] = relationship("Campaign", back_populates="leads")
    score: Mapped[LeadScore | None] = relationship(
        "LeadScore", back_populates="lead", uselist=False
    )
    messages: Mapped[list[Message]] = relationship("Message", back_populates="lead")
    conversation: Mapped[Conversation | None] = relationship(
        "Conversation", back_populates="lead", uselist=False
    )
    agent_state: Mapped[AgentState | None] = relationship(
        "AgentState", back_populates="lead", uselist=False
    )
    research: Mapped[ProspectResearch | None] = relationship(
        "ProspectResearch", back_populates="lead", uselist=False
    )
    approvals: Mapped[list[OutreachApproval]] = relationship(
        "OutreachApproval", back_populates="lead"
    )

    __table_args__ = (
        UniqueConstraint("prospect_id", "campaign_id", name="uq_lead_prospect_campaign"),
    )


class LeadScore(Base, TimestampMixin):
    __tablename__ = "lead_scores"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    total_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    industry_fit: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    seniority_fit: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    company_size_fit: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    email_confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    engagement_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    is_qualified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    qualification_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    scored_by: Mapped[str] = mapped_column(String(100), default="agent", nullable=False)
    scoring_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    lead: Mapped[Lead] = relationship("Lead", back_populates="score")


class Message(Base, TimestampMixin):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False
    )
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
    )
    direction: Mapped[MessageDirection] = mapped_column(
        Enum(MessageDirection), nullable=False
    )
    status: Mapped[MessageStatus] = mapped_column(
        Enum(MessageStatus), nullable=False, default=MessageStatus.DRAFT
    )
    subject: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    from_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    to_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reply_to: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider_message_id: Mapped[str | None] = mapped_column(String(500), nullable=True)  # Gmail/Outlook ID
    campaign_step_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("campaign_steps.id", ondelete="SET NULL"), nullable=True
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_auto_generated: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    generation_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    lead: Mapped[Lead] = relationship("Lead", back_populates="messages")
    conversation: Mapped[Conversation | None] = relationship(
        "Conversation", back_populates="messages"
    )

    __table_args__ = (
        Index("ix_messages_lead_direction", "lead_id", "direction"),
    )


class Conversation(Base, TimestampMixin):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    status: Mapped[ConversationStatus] = mapped_column(
        Enum(ConversationStatus), nullable=False, default=ConversationStatus.INACTIVE
    )
    assigned_to_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    last_reply_intent: Mapped[ReplyIntent | None] = mapped_column(
        Enum(ReplyIntent), nullable=True
    )
    escalated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    human_engaged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    subject: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    thread_id: Mapped[str | None] = mapped_column(String(500), nullable=True)  # provider thread ID
    ai_auto_respond: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    copilot_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    lead: Mapped[Lead] = relationship("Lead", back_populates="conversation")
    messages: Mapped[list[Message]] = relationship(
        "Message", back_populates="conversation", order_by="Message.created_at"
    )
    assigned_to: Mapped[User | None] = relationship("User", back_populates="conversations")
    events: Mapped[list[ConversationEvent]] = relationship(
        "ConversationEvent", back_populates="conversation", order_by="ConversationEvent.created_at"
    )


class ConversationEvent(Base):
    __tablename__ = "conversation_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    actor: Mapped[str] = mapped_column(String(100), nullable=False)  # "agent" | "human" | "system"
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    conversation: Mapped[Conversation] = relationship("Conversation", back_populates="events")


class KnowledgeDocument(Base, TimestampMixin):
    __tablename__ = "knowledge_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    doc_type: Mapped[str] = mapped_column(String(100), nullable=False)  # webpage | manual | faq | pdf
    doc_category: Mapped[str] = mapped_column(String(100), default="document", nullable=False)  # document | faq | messaging_rule | pricing_rule | prohibited_claim | case_study
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    ingested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    chunks: Mapped[list[KnowledgeChunk]] = relationship(
        "KnowledgeChunk", back_populates="document", cascade="all, delete-orphan"
    )


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    document: Mapped[KnowledgeDocument] = relationship("KnowledgeDocument", back_populates="chunks")

    __table_args__ = (
        Index(
            "ix_knowledge_chunks_embedding",
            "embedding",
            postgresql_using="ivfflat",
            postgresql_with={"lists": 100},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )


class AgentState(Base, TimestampMixin):
    __tablename__ = "agent_states"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    agent_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[AgentStatusEnum] = mapped_column(
        Enum(AgentStatusEnum), nullable=False, default=AgentStatusEnum.IDLE
    )
    state_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    lead: Mapped[Lead] = relationship("Lead", back_populates="agent_state")


class ProviderConfig(Base, TimestampMixin):
    """Encrypted storage for provider credentials that users configure via UI."""
    __tablename__ = "provider_configs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_type: Mapped[str] = mapped_column(String(100), nullable=False)  # llm | email | search | enrichment
    provider_name: Mapped[str] = mapped_column(String(100), nullable=False)  # openai | gmail | hunter
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    config_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # non-sensitive config
    encrypted_secrets: Mapped[str | None] = mapped_column(Text, nullable=True)  # Fernet-encrypted JSON
    updated_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    __table_args__ = (
        UniqueConstraint("provider_type", "provider_name", name="uq_provider_config"),
    )


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leads.id", ondelete="SET NULL"), nullable=True
    )
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True
    )
    notification_type: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[NotificationStatus] = mapped_column(
        Enum(NotificationStatus), nullable=False, default=NotificationStatus.PENDING
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    target_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    extra_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class AuditLog(Base):
    """Immutable audit trail — never updated, only inserted."""
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[AuditAction] = mapped_column(Enum(AuditAction), nullable=False)
    resource_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    user: Mapped[User | None] = relationship("User", back_populates="audit_logs")


# ── Phase 2 Extended Models ───────────────────────────────────────────────────

class ProspectResearch(Base, TimestampMixin):
    """Structured AI research intelligence record for a Lead/Prospect."""
    __tablename__ = "prospect_researches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    company_context: Mapped[str | None] = mapped_column(Text, nullable=True)
    recent_developments: Mapped[str | None] = mapped_column(Text, nullable=True)
    communication_signals: Mapped[str | None] = mapped_column(Text, nullable=True)
    potential_challenge: Mapped[str | None] = mapped_column(Text, nullable=True)
    potential_opportunity: Mapped[str | None] = mapped_column(Text, nullable=True)
    why_rayven_relevant: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_urls: Mapped[list | None] = mapped_column(JSON, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.8, nullable=False)
    raw_intelligence: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    lead: Mapped[Lead] = relationship("Lead", back_populates="research")


class EmailTemplate(Base, TimestampMixin):
    """Reusable strategic outreach email framework template library."""
    __tablename__ = "email_templates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), default="Initial Outreach", nullable=False)
    purpose: Mapped[str | None] = mapped_column(Text, nullable=True)
    when_to_use: Mapped[str | None] = mapped_column(Text, nullable=True)
    when_not_to_use: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommended_lead_types: Mapped[str | None] = mapped_column(Text, nullable=True)
    subject_template: Mapped[str] = mapped_column(String(1000), nullable=False)
    body_template: Mapped[str] = mapped_column(Text, nullable=False)
    rules: Mapped[str | None] = mapped_column(Text, nullable=True)
    tone: Mapped[str | None] = mapped_column(String(100), default="Consultative & Direct", nullable=True)
    max_length: Mapped[str | None] = mapped_column(String(50), default="150 words", nullable=True)
    cta_style: Mapped[str | None] = mapped_column(String(100), default="Low-pressure conversational", nullable=True)
    follow_up_rules: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    variables: Mapped[list | None] = mapped_column(JSON, nullable=True)
    rayven_capabilities: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


class Suppression(Base, TimestampMixin):
    """Global domain and email blocklist for compliance/safety."""
    __tablename__ = "suppressions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    suppression_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "email" | "domain"
    value: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    added_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    __table_args__ = (
        UniqueConstraint("suppression_type", "value", name="uq_suppression_type_val"),
    )


class DiscoveryJob(Base, TimestampMixin):
    """Track background lead discovery executions."""
    __tablename__ = "discovery_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)  # pending|running|completed|failed
    query: Mapped[str] = mapped_column(Text, nullable=False)
    sources: Mapped[list | None] = mapped_column(JSON, nullable=True)
    results_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class OutreachApproval(Base, TimestampMixin):
    """Queue of draft emails requiring human review (when approval_mode is manual)."""
    __tablename__ = "outreach_approvals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False
    )
    campaign_step_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("campaign_steps.id", ondelete="SET NULL"), nullable=True
    )
    subject: Mapped[str] = mapped_column(String(1000), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)  # pending|approved|rejected|edited
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    lead: Mapped[Lead] = relationship("Lead", back_populates="approvals")

