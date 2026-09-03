"""
Sequence Orchestration Agent
Drives the autonomous campaign lifecycle loop for all active campaigns.
Enforces send windows, daily limits, multi-step follow-ups, and automatic sequence stopping.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.discovery_agent import run_discovery_agent
from app.agents.enrichment_agent import run_enrichment_agent
from app.agents.research_agent import run_research_agent
from app.agents.scoring_agent import run_scoring_agent
from app.agents.writer_agent import run_writer_agent
from app.models import Campaign, CampaignStatus, Lead, LeadStatus, Prospect
from app.providers.registry import get_email_provider
from app.services.outreach import OutreachService
from app.services.safety import is_global_kill_switch_active

logger = logging.getLogger(__name__)


async def run_sequence_agent_tick(db: AsyncSession) -> dict:
    """Execute a single cycle (tick) of the campaign orchestration loop."""
    if is_global_kill_switch_active():
        logger.warning("Sequence tick skipped: Global kill switch is ACTIVE.")
        return {"skipped": True, "reason": "Kill switch active"}

    # Fetch all active campaigns
    stmt = select(Campaign).where(Campaign.status == CampaignStatus.ACTIVE)
    res = await db.execute(stmt)
    campaigns = res.scalars().all()

    stats = {"campaigns_processed": len(campaigns), "leads_advanced": 0, "messages_sent": 0}
    outreach_service = OutreachService(db)
    email_provider = get_email_provider()

    now_utc = datetime.now(UTC)

    for campaign in campaigns:
        # Check send window (local hour check, default 9 to 17)
        current_hour = now_utc.hour
        if not (campaign.send_window_start <= current_hour <= campaign.send_window_end) and not campaign.test_mode:
            logger.info(f"Campaign {campaign.id} outside send window ({campaign.send_window_start}-{campaign.send_window_end}h, now {current_hour}h)")
            continue

        # Check daily limit
        if campaign.daily_sends_today >= campaign.daily_send_limit:
            logger.info(f"Campaign {campaign.id} daily limit reached ({campaign.daily_sends_today}/{campaign.daily_send_limit})")
            continue

        from sqlalchemy.orm import selectinload
        # Fetch leads for this campaign that are ready to advance
        lead_stmt = (
            select(Lead)
            .where(
                Lead.campaign_id == campaign.id,
                Lead.is_stopped == False,
            )
            .options(
                selectinload(Lead.prospect).selectinload(Prospect.company),
                selectinload(Lead.campaign),
                selectinload(Lead.research),
                selectinload(Lead.score),
            )
        )
        lead_res = await db.execute(lead_stmt)
        leads = lead_res.scalars().all()

        for lead in leads:
            # 1. Pipeline Advancement Pipeline
            try:
                if lead.status in (LeadStatus.DISCOVERED, LeadStatus.NEW):
                    # Run Research Agent
                    await run_research_agent(db, lead.id)
                    stats["leads_advanced"] += 1

                if lead.status == LeadStatus.RESEARCHED:
                    # Run Enrichment Agent
                    await run_enrichment_agent(db, lead.id)
                    stats["leads_advanced"] += 1

                if lead.status == LeadStatus.ENRICHED:
                    # Run Scoring Agent
                    await run_scoring_agent(db, lead.id)
                    stats["leads_advanced"] += 1

                if lead.status == LeadStatus.QUALIFIED and lead.current_step == 0:
                    # Run Writer Agent for Step 1 Initial Outreach
                    await run_writer_agent(db, lead.id, step_number=1)
                    stats["leads_advanced"] += 1

                if lead.status == LeadStatus.OUTREACH_PENDING:
                    # Execute Send
                    send_res = await outreach_service.send_lead_message(
                        lead_id=lead.id,
                        email_provider=email_provider,
                    )
                    if send_res.get("success"):
                        lead.current_step = max(lead.current_step, 1)
                        lead.next_action_at = now_utc + timedelta(hours=campaign.follow_up_delay_hours)
                        stats["messages_sent"] += 1

                elif lead.status == LeadStatus.OUTREACH_SENT:
                    # Check if due for follow-up
                    if lead.next_action_at and now_utc >= lead.next_action_at:
                        if lead.current_step < (campaign.max_follow_ups + 1):
                            next_step = lead.current_step + 1
                            logger.info(f"Generating follow-up #{next_step} for lead {lead.id}")
                            await run_writer_agent(db, lead.id, step_number=next_step)
                            lead.current_step = next_step
                            stats["leads_advanced"] += 1

            except Exception as e:
                logger.error(f"Error advancing lead {lead.id} in campaign {campaign.id}: {e}", exc_info=True)

        campaign.last_tick_at = now_utc
        await db.commit()

    return stats
