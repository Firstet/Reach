"""
Background Celery tasks for Reach outbound engine.
"""

from __future__ import annotations

import asyncio
import logging

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="run_campaign_tick")
def task_run_campaign_tick():
    """Execute sequence orchestration tick across all active campaigns."""
    async def _run():
        from app.core.database import AsyncSessionLocal
        from app.agents.sequence_agent import run_sequence_agent_tick

        async with AsyncSessionLocal() as db:
            return await run_sequence_agent_tick(db)

    return asyncio.run(_run())


@celery_app.task(name="run_discovery_job")
def task_run_discovery_job(campaign_id: str, job_id: str | None = None):
    """Run lead discovery agent."""
    async def _run():
        import uuid
        from app.core.database import AsyncSessionLocal
        from app.agents.discovery_agent import run_discovery_agent

        async with AsyncSessionLocal() as db:
            return await run_discovery_agent(
                db,
                campaign_id=uuid.UUID(campaign_id),
                job_id=uuid.UUID(job_id) if job_id else None,
            )

    return asyncio.run(_run())


@celery_app.task(name="research_lead")
def task_research_lead(lead_id: str):
    """Run research agent on a single lead."""
    async def _run():
        import uuid
        from app.core.database import AsyncSessionLocal
        from app.agents.research_agent import run_research_agent

        async with AsyncSessionLocal() as db:
            return await run_research_agent(db, uuid.UUID(lead_id))

    return asyncio.run(_run())


@celery_app.task(name="enrich_lead")
def task_enrich_lead(lead_id: str):
    """Run enrichment agent on a single lead."""
    async def _run():
        import uuid
        from app.core.database import AsyncSessionLocal
        from app.agents.enrichment_agent import run_enrichment_agent

        async with AsyncSessionLocal() as db:
            return await run_enrichment_agent(db, uuid.UUID(lead_id))

    return asyncio.run(_run())


@celery_app.task(name="score_lead")
def task_score_lead(lead_id: str):
    """Run scoring agent on a single lead."""
    async def _run():
        import uuid
        from app.core.database import AsyncSessionLocal
        from app.agents.scoring_agent import run_scoring_agent

        async with AsyncSessionLocal() as db:
            return await run_scoring_agent(db, uuid.UUID(lead_id))

    return asyncio.run(_run())


@celery_app.task(name="generate_draft")
def task_generate_draft(lead_id: str, step_num: int = 1):
    """Run writer agent to generate personalized outreach draft."""
    async def _run():
        import uuid
        from app.core.database import AsyncSessionLocal
        from app.agents.writer_agent import run_writer_agent

        async with AsyncSessionLocal() as db:
            return await run_writer_agent(db, uuid.UUID(lead_id), step_number=step_num)

    return asyncio.run(_run())


@celery_app.task(name="fetch_and_process_replies")
def task_fetch_and_process_replies():
    """Poll inbox for replies and run Conversation Engine."""
    async def _run():
        from app.core.database import AsyncSessionLocal
        from app.agents.reply_agent import run_reply_agent

        async with AsyncSessionLocal() as db:
            return await run_reply_agent(db, since_hours=24)

    return asyncio.run(_run())


@celery_app.task(name="ingest_knowledge_base")
def task_ingest_knowledge_base(force: bool = False):
    """Trigger knowledge base ingestion."""
    async def _run():
        from app.core.database import AsyncSessionLocal
        from app.knowledge.ingestion import ingest_knowledge_base
        from app.providers.registry import get_llm_provider

        async with AsyncSessionLocal() as db:
            llm = get_llm_provider()
            stats = await ingest_knowledge_base(db, llm, force_reingest=force)
            logger.info(f"Knowledge base ingestion complete: {stats}")
            return stats

    return asyncio.run(_run())
