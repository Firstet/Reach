"""
Provider registry — resolves and returns the configured provider instances.
This is the single place where provider selection logic lives.
"""

from __future__ import annotations

import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)
def get_llm_provider():
    """Return the configured LLM provider instance."""
    settings = get_settings()
    name = settings.active_llm_provider
    if name == "openai":
        from app.providers.llm.openai_provider import OpenAIProvider
        return OpenAIProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            embedding_model=settings.openai_embedding_model,
        )
    elif name == "anthropic":
        from app.providers.llm.anthropic_provider import AnthropicProvider
        return AnthropicProvider(
            api_key=settings.anthropic_api_key,
            model=settings.anthropic_model,
        )
    elif name == "openai_compatible":
        from app.providers.llm.openai_compatible_provider import OpenAICompatibleProvider
        return OpenAICompatibleProvider(
            base_url=settings.openai_compatible_base_url,
            api_key=settings.openai_compatible_api_key,
            model=settings.openai_compatible_model,
            embedding_model=settings.openai_compatible_embedding_model,
        )
    else:
        logger.warning(f"Unknown LLM provider '{name}', defaulting to OpenAI stub.")
        from app.providers.llm.openai_provider import OpenAIProvider
        return OpenAIProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            embedding_model=settings.openai_embedding_model,
        )


def get_search_provider():
    """Return the configured search provider instance."""
    settings = get_settings()
    name = settings.active_search_provider
    if name == "serper":
        from app.providers.search.serper_provider import SerperProvider
        return SerperProvider(api_key=settings.serper_api_key)
    else:
        return None


def get_enrichment_provider():
    """Return the configured enrichment provider instance (defaults to NoEnrichmentProvider)."""
    settings = get_settings()
    name = settings.active_enrichment_provider
    if name == "hunter":
        from app.providers.enrichment.hunter_provider import HunterProvider
        return HunterProvider(api_key=settings.hunter_api_key)
    elif name == "apollo":
        from app.providers.enrichment.apollo_provider import ApolloProvider
        return ApolloProvider(api_key=settings.apollo_api_key)
    else:
        from app.providers.enrichment.no_enrichment_provider import NoEnrichmentProvider
        return NoEnrichmentProvider()


def get_email_provider():
    """Return the configured email provider instance."""
    settings = get_settings()
    name = settings.active_email_provider
    if name == "gmail":
        from app.providers.email.gmail_provider import GmailProvider
        return GmailProvider(
            client_id=settings.gmail_client_id,
            client_secret=settings.gmail_client_secret,
            refresh_token=settings.gmail_refresh_token,
            sender_email=settings.gmail_sender_email,
        )
    elif name == "smtp":
        from app.providers.email.smtp_provider import SMTPProvider
        return SMTPProvider(
            host=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_username,
            password=settings.smtp_password,
            use_tls=settings.smtp_use_tls,
            sender_email=settings.smtp_sender_email or settings.smtp_username,
        )
    else:
        return None




def get_linkedin_provider():
    """Return the LinkedIn provider (or disabled stub)."""
    if not _settings.linkedin_enabled:
        from app.providers.linkedin.playwright_provider import DisabledLinkedInProvider
        return DisabledLinkedInProvider()
    from app.providers.linkedin.playwright_provider import PlaywrightLinkedInProvider
    return PlaywrightLinkedInProvider(
        session_cookie=_settings.linkedin_session_cookie,
        rate_limit_per_hour=_settings.linkedin_rate_limit_per_hour,
        delay_min_ms=_settings.linkedin_human_delay_min_ms,
        delay_max_ms=_settings.linkedin_human_delay_max_ms,
        enabled=True,
    )


def get_notification_provider(email_provider=None):
    """Return the configured notification provider instance."""
    name = _settings.active_notification_provider
    if name == "slack":
        from app.providers.notification.notification_providers import SlackNotificationProvider
        return SlackNotificationProvider(
            webhook_url=_settings.slack_webhook_url,
            channel=_settings.slack_notification_channel,
        )
    elif name == "webhook":
        from app.providers.notification.notification_providers import WebhookNotificationProvider
        return WebhookNotificationProvider(
            webhook_url=_settings.notification_webhook_url,
            secret=_settings.notification_webhook_secret,
        )
    else:
        from app.providers.notification.notification_providers import EmailNotificationProvider
        ep = email_provider or get_email_provider()
        return EmailNotificationProvider(
            escalation_email=_settings.escalation_email,
            email_provider=ep,
        )
