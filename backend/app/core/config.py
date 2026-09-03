"""
Reach — AI Business Development Agent for RayvenSC
Application settings and configuration management.
"""

from __future__ import annotations

import secrets
from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────────
    app_name: str = "Reach"
    app_env: Literal["development", "production", "test"] = "development"
    app_secret_key: str = Field(default_factory=lambda: secrets.token_hex(32))
    app_debug: bool = False
    app_port: int = 8000
    frontend_url: str = "http://localhost:3000"
    cors_origins: list[str] | str = Field(default_factory=lambda: ["http://localhost:3000"])

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list) -> list[str]:
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                try:
                    import json
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed]
                except Exception:
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        if isinstance(v, list):
            return [str(item).strip() for item in v]
        return ["http://localhost:3000"]

    # ── Database ─────────────────────────────────────────────────────────────
    database_url: str = "sqlite+aiosqlite:///./reach.db"
    database_sync_url: str = "sqlite:///./reach.db"
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # ── Redis ─────────────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # ── Authentication ────────────────────────────────────────────────────────
    jwt_secret_key: str = Field(default_factory=lambda: secrets.token_hex(32))
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7
    admin_email: str = "admin@rayvensc.com"
    admin_password: str = "changeme"

    # ── LLM Provider ─────────────────────────────────────────────────────────
    active_llm_provider: Literal["openai", "anthropic", "gemini", "local", "openai_compatible"] = "openai"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-pro"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"
    openai_compatible_base_url: str = "https://api.groq.com/openai/v1"
    openai_compatible_api_key: str = ""
    openai_compatible_model: str = "llama-3.3-70b-versatile"
    openai_compatible_embedding_model: str = "text-embedding-3-small"

    # ── Email Provider ────────────────────────────────────────────────────────
    active_email_provider: Literal["gmail", "outlook", "smtp"] = "gmail"
    gmail_client_id: str = ""
    gmail_client_secret: str = ""
    gmail_refresh_token: str = ""
    gmail_sender_email: str = ""
    outlook_client_id: str = ""
    outlook_client_secret: str = ""
    outlook_tenant_id: str = ""
    outlook_sender_email: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    smtp_sender_email: str = ""

    # ── Search Provider ───────────────────────────────────────────────────────
    active_search_provider: Literal["serper", "serpapi", "brave", "none"] = "none"
    serper_api_key: str = ""
    serpapi_api_key: str = ""
    brave_search_api_key: str = ""

    # ── Enrichment Provider ───────────────────────────────────────────────────
    active_enrichment_provider: Literal[
        "none", "hunter", "apollo", "clearbit"
    ] = "none"
    email_policy: Literal["verified_only", "high_confidence", "any_email"] = "verified_only"
    hunter_api_key: str = ""
    apollo_api_key: str = ""
    clearbit_api_key: str = ""


    # ── LinkedIn ──────────────────────────────────────────────────────────────
    linkedin_enabled: bool = False
    linkedin_session_cookie: str = ""
    linkedin_rate_limit_per_hour: int = 20
    linkedin_human_delay_min_ms: int = 2000
    linkedin_human_delay_max_ms: int = 8000

    # ── Notifications ─────────────────────────────────────────────────────────
    active_notification_provider: Literal[
        "email", "slack", "webhook", "none"
    ] = "email"
    slack_webhook_url: str = ""
    slack_notification_channel: str = "#bd-alerts"
    notification_webhook_url: str = ""
    notification_webhook_secret: str = ""
    escalation_email: str = "hello@rayvensc.com"

    # ── Vector Store ──────────────────────────────────────────────────────────
    vector_dimensions: int = 1536
    vector_similarity_threshold: float = 0.75

    # ── Campaign & Sending Limits ─────────────────────────────────────────────
    default_follow_up_delay_hours: int = 72
    default_max_follow_ups: int = 3
    default_send_window_start: int = 9
    default_send_window_end: int = 17
    default_daily_send_limit: int = 5
    monthly_send_limit: int = 50
    unsubscribe_link_enabled: bool = True

    # ── RayvenSC Pre-filled Branding Copy ─────────────────────────────────────
    rayvensc_company_name: str = "Rayven Strategic Communications"
    rayvensc_tagline: str = "Context Intelligence · Narrative Architecture · Strategic Deployment"
    rayvensc_logo_url: str = "https://rayvensc.com/logo.png"
    rayvensc_sender_persona: str = "Executive & Founder Advisory Voice"
    rayvensc_website_pitch_angle: str = "We craft modern, high-trust digital platforms and web applications for enterprise leaders that establish instant authority and digital growth."
    rayvensc_pr_pitch_angle: str = "We architect corporate narratives, securing tier-1 media positioning, PR coverage, and executive reputation management across target markets."
    rayvensc_founder_pitch_angle: str = "We build personal brand positioning for CEOs, Founders, and C-Suite leaders to transform executive presence into high-trust inbound partnerships."
    rayvensc_email_footer_html: str = "<p>Warm regards,<br/><strong>Rayven Strategic Communications</strong><br/>Abuja, Nigeria · <a href='https://rayvensc.com'>rayvensc.com</a></p>"


    # ── Security ──────────────────────────────────────────────────────────────
    encryption_key: str = ""  # Fernet key
    max_login_attempts: int = 5
    rate_limit_requests_per_minute: int = 60

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
