"""Configuration management routes — encrypted credential storage."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routers.auth import get_current_user
from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import decrypt_secret, encrypt_secret

from app.models import AuditAction, AuditLog, ProviderConfig, User, UserRole
from app.providers.registry import (
    get_email_provider,
    get_enrichment_provider,
    get_llm_provider,
    get_notification_provider,
    get_search_provider,
)

router = APIRouter(prefix="/config", tags=["config"])


class ProviderConfigUpdate(BaseModel):
    provider_type: str  # llm | email | search | enrichment | linkedin | notification
    provider_name: str  # openai | gmail | hunter | serper | slack
    is_active: bool = True
    config_data: dict = {}
    secrets: dict = {}  # Will be encrypted before storage


def _mask_secrets(secrets: dict) -> dict:
    """Return secrets with values masked for display."""
    return {k: "***" if v else "" for k, v in secrets.items()}


@router.get("/public")
async def get_public_config(db: AsyncSession = Depends(get_db)):
    """Return non-secret public customization configurations (e.g. home_customization, branding)."""
    result = await db.execute(
        select(ProviderConfig).where(ProviderConfig.provider_type.in_(["appearance", "branding"]))
    )
    configs = result.scalars().all()
    providers = []
    for c in configs:
        providers.append({
            "provider_type": c.provider_type,
            "provider_name": c.provider_name,
            "config_data": c.config_data,
        })
    return {"providers": providers}


@router.get("")
async def get_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return all provider configurations (secrets masked)."""
    result = await db.execute(select(ProviderConfig))
    configs = result.scalars().all()

    providers = []
    for c in configs:
        secrets_display = {}
        if c.encrypted_secrets:
            try:
                raw = json.loads(decrypt_secret(c.encrypted_secrets))
                secrets_display = _mask_secrets(raw)
            except Exception:
                secrets_display = {}

        providers.append({
            "id": str(c.id),
            "provider_type": c.provider_type,
            "provider_name": c.provider_name,
            "is_active": c.is_active,
            "config_data": c.config_data,
            "secrets": secrets_display,
            "updated_at": c.updated_at.isoformat(),
        })

    settings = get_settings()

    # Sync runtime settings with active ProviderConfig rows from DB
    for c in configs:
        if c.is_active:
            secrets = {}
            if c.encrypted_secrets:
                try:
                    secrets = json.loads(decrypt_secret(c.encrypted_secrets))
                except Exception:
                    secrets = {}
            cfg = c.config_data or {}

            if c.provider_type == "llm":
                settings.active_llm_provider = c.provider_name
                if secrets.get("api_key"):
                    if c.provider_name == "openai":
                        settings.openai_api_key = secrets["api_key"]
                    elif c.provider_name == "openai_compatible":
                        settings.openai_compatible_api_key = secrets["api_key"]
                    elif c.provider_name == "anthropic":
                        settings.anthropic_api_key = secrets["api_key"]
                    elif c.provider_name == "gemini":
                        settings.gemini_api_key = secrets["api_key"]
            elif c.provider_type == "search":
                if secrets.get("api_key"):
                    settings.serper_api_key = secrets["api_key"]
            elif c.provider_type == "email":
                if cfg.get("smtp_host"):
                    settings.smtp_host = cfg["smtp_host"]
                if cfg.get("smtp_username"):
                    settings.smtp_username = cfg["smtp_username"]
                if secrets.get("smtp_password"):
                    settings.smtp_password = secrets["smtp_password"]
                if cfg.get("email_signature_text"):
                    settings.email_signature_text = cfg["email_signature_text"]
                if cfg.get("email_signature_html"):
                    settings.email_signature_html = cfg["email_signature_html"]

    has_custom_llm_key = bool(
        settings.openai_api_key
        or settings.anthropic_api_key
        or settings.gemini_api_key
        or settings.openai_compatible_api_key
    )
    email_configured = bool(
        (settings.smtp_host and settings.smtp_username)
        or settings.gmail_refresh_token
        or settings.outlook_client_id
    )

    engine_status = {
        "llm_configured": True,  # Standby / Local LLM provider is always ready
        "has_custom_llm_key": has_custom_llm_key,
        "search_configured": True,  # DuckDuckGo zero-cost fallback active
        "serper_api_key_set": bool(settings.serper_api_key),
        "email_configured": email_configured,
        "openai_api_key_set": has_custom_llm_key,
        "smtp_host_set": bool(settings.smtp_host and settings.smtp_username),
        "gmail_refresh_token_set": bool(settings.gmail_refresh_token),
        "active_llm_provider": settings.active_llm_provider,
        "active_search_provider": settings.active_search_provider if settings.serper_api_key else "duckduckgo (Zero-Cost)",
        "active_email_provider": settings.active_email_provider if email_configured else "standby",
    }

    return {"providers": providers, "engine_status": engine_status}


@router.put("")
async def update_config(
    body: ProviderConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upsert a provider configuration. Secrets are encrypted at rest."""
    if current_user.role not in (UserRole.ADMIN, UserRole.OPERATOR):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    # If set active, set other providers of the same type to inactive
    if body.is_active:
        existing_type = await db.execute(
            select(ProviderConfig).where(
                ProviderConfig.provider_type == body.provider_type,
                ProviderConfig.provider_name != body.provider_name,
            )
        )
        for other in existing_type.scalars().all():
            other.is_active = False

    result = await db.execute(
        select(ProviderConfig).where(
            ProviderConfig.provider_type == body.provider_type,
            ProviderConfig.provider_name == body.provider_name,
        )
    )
    config = result.scalar_one_or_none()

    encrypted = encrypt_secret(json.dumps(body.secrets)) if body.secrets else None

    if config:
        config.is_active = body.is_active
        config.config_data = body.config_data
        if body.secrets:
            # Merge with existing secrets (don't overwrite with empty)
            try:
                existing = json.loads(decrypt_secret(config.encrypted_secrets)) if config.encrypted_secrets else {}
            except Exception:
                existing = {}
            merged = {**existing, **{k: v for k, v in body.secrets.items() if v}}
            config.encrypted_secrets = encrypt_secret(json.dumps(merged))
        config.updated_by_id = current_user.id
    else:
        import uuid
        config = ProviderConfig(
            id=uuid.uuid4(),
            provider_type=body.provider_type,
            provider_name=body.provider_name,
            is_active=body.is_active,
            config_data=body.config_data,
            encrypted_secrets=encrypted,
            updated_by_id=current_user.id,
        )
        db.add(config)

    # Sync runtime settings in memory
    from app.core.config import get_settings
    settings = get_settings()
    if body.provider_type == "llm" and body.is_active:
        settings.active_llm_provider = body.provider_name
        if body.provider_name == "openai_compatible":
            if "base_url" in body.config_data:
                settings.openai_compatible_base_url = body.config_data["base_url"]
            if "model" in body.config_data:
                settings.openai_compatible_model = body.config_data["model"]
            if "embedding_model" in body.config_data:
                settings.openai_compatible_embedding_model = body.config_data["embedding_model"]
            if "api_key" in body.secrets and body.secrets["api_key"]:
                settings.openai_compatible_api_key = body.secrets["api_key"]
    elif body.provider_type == "email" and body.is_active:
        settings.active_email_provider = body.provider_name
        if body.provider_name == "smtp":
            if "smtp_host" in body.config_data:
                settings.smtp_host = body.config_data["smtp_host"]
            if "smtp_port" in body.config_data and body.config_data["smtp_port"]:
                settings.smtp_port = int(body.config_data["smtp_port"])
            if "smtp_username" in body.config_data:
                settings.smtp_username = body.config_data["smtp_username"]
            if "sender_email" in body.config_data:
                settings.smtp_sender_email = body.config_data["sender_email"]
            if "smtp_password" in body.secrets and body.secrets["smtp_password"]:
                settings.smtp_password = body.secrets["smtp_password"]

    db.add(AuditLog(
        user_id=current_user.id,
        action=AuditAction.CONFIG_UPDATED,
        details={"provider_type": body.provider_type, "provider_name": body.provider_name},
    ))
    await db.commit()
    return {"status": "updated", "provider": body.provider_name}



@router.get("/health")
async def provider_health(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run health checks on all active providers configured in database."""
    # Sync runtime settings with latest active ProviderConfig from DB
    stmt = select(ProviderConfig).where(ProviderConfig.is_active == True)
    result = await db.execute(stmt)
    active_configs = result.scalars().all()

    settings = get_settings()
    for pc in active_configs:
        secrets = {}
        if pc.encrypted_secrets:
            try:
                secrets = json.loads(decrypt_secret(pc.encrypted_secrets))
            except Exception:
                secrets = {}
        cfg = pc.config_data or {}


        if pc.provider_type == "llm":
            settings.active_llm_provider = pc.provider_name
            if pc.provider_name == "openai_compatible":
                if cfg.get("base_url"): settings.openai_compatible_base_url = cfg["base_url"]
                if secrets.get("api_key"): settings.openai_compatible_api_key = secrets["api_key"]
                if cfg.get("model"): settings.openai_compatible_model = cfg["model"]
            elif pc.provider_name == "openai":
                if secrets.get("api_key"): settings.openai_api_key = secrets["api_key"]
                if cfg.get("model"): settings.openai_model = cfg["model"]
        elif pc.provider_type == "search":
            settings.active_search_provider = pc.provider_name
            if secrets.get("api_key"): settings.serper_api_key = secrets["api_key"]
        elif pc.provider_type == "enrichment":
            settings.active_enrichment_provider = pc.provider_name
            if secrets.get("api_key"): settings.hunter_api_key = secrets["api_key"]
        elif pc.provider_type == "email":
            settings.active_email_provider = pc.provider_name
            if cfg.get("smtp_host"): settings.smtp_host = cfg["smtp_host"]
            if cfg.get("smtp_port"): settings.smtp_port = int(cfg["smtp_port"]) if str(cfg["smtp_port"]).isdigit() else 587
            if cfg.get("smtp_username"): settings.smtp_username = cfg["smtp_username"]
            if secrets.get("smtp_password"): settings.smtp_password = secrets["smtp_password"]

    checks = {}

    try:
        llm = get_llm_provider()
        healthy = await llm.health_check()
        checks["llm"] = {"name": llm.provider_name, "healthy": healthy}
    except Exception as e:
        checks["llm"] = {"name": settings.active_llm_provider, "healthy": False, "error": str(e)}

    try:
        search = get_search_provider()
        if search:
            checks["search"] = {"name": search.provider_name, "healthy": await search.health_check()}
        else:
            checks["search"] = {"name": "none", "healthy": True, "note": "Zero-Paid search fallback active"}
    except Exception as e:
        checks["search"] = {"name": settings.active_search_provider, "healthy": False, "error": str(e)}

    try:
        enrichment = get_enrichment_provider()
        checks["enrichment"] = {"name": enrichment.provider_name, "healthy": await enrichment.health_check()}
    except Exception as e:
        checks["enrichment"] = {"name": settings.active_enrichment_provider, "healthy": False, "error": str(e)}

    try:
        email = get_email_provider()
        if email:
            checks["email"] = {"name": email.provider_name, "healthy": await email.health_check()}
        else:
            checks["email"] = {"name": "none", "healthy": True, "note": "Standby mode"}
    except Exception as e:
        checks["email"] = {"name": settings.active_email_provider, "healthy": False, "error": str(e)}

    all_healthy = all(v.get("healthy", False) for v in checks.values())
    return {"overall": "healthy" if all_healthy else "degraded", "providers": checks}

