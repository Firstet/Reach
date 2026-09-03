"""
Reach — AI Business Development Agent for RayvenSC
FastAPI Application Entry Point
"""

from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.database import engine, AsyncSessionLocal
from app.core.security import hash_password

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: startup → yield → shutdown."""
    logger.info("Starting Reach API...")

    # Create all tables (in development; use Alembic in production)
    if settings.is_development:
        from app.core.database import Base
        import app.models.models  # noqa: F401 — register all models
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created/verified.")

    # Ensure admin user exists
    await _ensure_admin()

    yield

    # Cleanup
    await engine.dispose()
    logger.info("Reach API shutdown complete.")


async def _ensure_admin():
    """Create the initial admin user if it doesn't exist."""
    from sqlalchemy import select
    from app.models import User, UserRole

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.email == settings.admin_email)
        )
        if not result.scalar_one_or_none():
            admin = User(
                id=uuid.uuid4(),
                email=settings.admin_email,
                hashed_password=hash_password(settings.admin_password),
                full_name="Admin",
                role=UserRole.ADMIN,
                is_active=True,
            )
            db.add(admin)
            await db.commit()
            logger.info(f"Admin user created: {settings.admin_email}")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Reach — RayvenSC AI Business Development Agent",
        description="AI-powered outbound business development platform for Rayven Strategic Communications",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/api/docs" if settings.is_development else None,
        redoc_url="/api/redoc" if settings.is_development else None,
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routes ────────────────────────────────────────────────────────────────
    from app.api.routers import (
        audit,
        auth,
        campaigns,
        config,
        conversations,
        discovery,
        knowledge,
        leads,
        outreach,
        prospects,
        scoring,
        suppression,
        templates,
        test_mode,
        knowledge_mgmt,
        crm,
    )
    from app.api.ws.notifications import router as ws_router

    prefix = "/api/v1"
    app.include_router(auth.router, prefix=prefix)
    app.include_router(campaigns.router, prefix=prefix)
    app.include_router(leads.router, prefix=prefix)
    app.include_router(prospects.companies_router, prefix=prefix)
    app.include_router(prospects.prospects_router, prefix=prefix)
    app.include_router(conversations.router, prefix=prefix)
    app.include_router(knowledge.router, prefix=prefix)
    app.include_router(knowledge_mgmt.router, prefix=prefix)
    app.include_router(crm.router, prefix=prefix)
    app.include_router(config.router, prefix=prefix)
    app.include_router(audit.router, prefix=prefix)
    app.include_router(discovery.router, prefix=prefix)
    app.include_router(outreach.router, prefix=prefix)
    app.include_router(templates.router, prefix=prefix)
    app.include_router(suppression.admin_router, prefix=prefix)
    app.include_router(suppression.router, prefix=prefix)
    app.include_router(test_mode.router, prefix=prefix)
    app.include_router(scoring.router, prefix=prefix)
    app.include_router(ws_router)  # WebSocket at /api/v1/ws/notifications

    # ── Safety Kill Switch Endpoints ──────────────────────────────────────────
    from app.services.safety import is_global_kill_switch_active, set_global_kill_switch

    @app.get(f"{prefix}/safety/kill-switch")
    async def get_kill_switch():
        return {"kill_switch_active": is_global_kill_switch_active()}

    @app.post(f"{prefix}/safety/kill-switch")
    async def toggle_kill_switch(active: bool):
        set_global_kill_switch(active)
        return {"kill_switch_active": is_global_kill_switch_active(), "message": "Kill switch updated"}

    # ── Health ────────────────────────────────────────────────────────────────
    @app.get("/health")
    async def health():
        return {"status": "ok", "service": "reach-api", "version": "1.0.0"}

    # ── Error Handlers ────────────────────────────────────────────────────────
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    return app


app = create_app()
