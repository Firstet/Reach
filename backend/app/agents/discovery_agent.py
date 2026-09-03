"""
Discovery Agent
Orchestrates lead discovery for a campaign using structured criteria parsing,
web search, LinkedIn (if enabled), and test-mode simulation.
"""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditAction, AuditLog, Campaign, DiscoveryJob
from app.providers.registry import get_llm_provider, get_search_provider
from app.services.discovery import DiscoveryService

logger = logging.getLogger(__name__)


async def run_discovery_agent(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    job_id: uuid.UUID | None = None,
) -> dict:
    """Run the lead discovery workflow for a campaign."""
    campaign = await db.get(Campaign, campaign_id)
    if not campaign:
        raise ValueError(f"Campaign {campaign_id} not found")

    query_text = campaign.discovery_query or campaign.description or f"Find leaders in {campaign.target_industry or 'Tech'} in {campaign.target_location or 'Nigeria'}"

    # Get or create DiscoveryJob record
    job = None
    if job_id:
        job = await db.get(DiscoveryJob, job_id)
    if not job:
        job = DiscoveryJob(
            id=uuid.uuid4(),
            campaign_id=campaign_id,
            status="running",
            query=query_text,
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
    else:
        job.status = "running"
        await db.commit()

    service = DiscoveryService(db)
    llm = get_llm_provider()
    search = get_search_provider()

    discovered_count = 0
    try:
        if campaign.test_mode:
            # TEST MODE: Create 3 realistic simulated prospects
            logger.info(f"[TEST MODE] Simulating discovery for campaign {campaign_id}")
            test_prospects = [
                {"first_name": "Amina", "last_name": "Bello", "title": "Chief Executive Officer", "company": "PayWave Tech", "domain": "paywavetech.ng", "industry": "Finance", "email": "amina.bello@paywavetech.ng"},
                {"first_name": "Emeka", "last_name": "Okonkwo", "title": "Chief Marketing Officer", "company": "Apex Health Systems", "domain": "apexhealth.ng", "industry": "Healthcare", "email": "emeka.o@apexhealth.ng"},
                {"first_name": "Tunde", "last_name": "Adeyemi", "title": "Head of Corporate Communications", "company": "Kestrel Energy Africa", "domain": "kestrelenergy.com", "industry": "Energy", "email": "tadeyemi@kestrelenergy.com"},
            ]
            lead_ids = await service.ingest_csv_prospects(test_prospects, campaign_id)
            # Mark leads as test mode
            for lid in lead_ids:
                from app.models import Lead
                lead = await db.get(Lead, lid)
                if lead:
                    lead.is_test = True
            await db.commit()
            discovered_count = len(lead_ids)
        else:
            # REAL DISCOVERY MODE
            criteria = await service.parse_campaign_query(query_text, llm)
            prospects = await service.discover_via_search(criteria, search, max_results=15)

            for p in prospects:
                company = await service._get_or_create_company(
                    name=p.company_name or f"{p.last_name} Enterprise",
                    domain=p.company_domain,
                )
                prospect = await service._get_or_create_prospect(
                    company_id=company.id,
                    first_name=p.first_name,
                    last_name=p.last_name,
                    title=p.title,
                    linkedin_url=p.linkedin_url,
                    source=p.source,
                )
                lead = await service._enroll_lead(prospect.id, campaign_id, source=p.source)
                if lead:
                    discovered_count += 1
            await db.commit()

        job.status = "completed"
        job.results_count = discovered_count
        db.add(AuditLog(
            action=AuditAction.AGENT_COMPLETED,
            resource_type="discovery_job",
            resource_id=str(job.id),
            details={"campaign_id": str(campaign_id), "discovered": discovered_count, "test_mode": campaign.test_mode},
        ))
        await db.commit()
        return {"job_id": str(job.id), "status": "completed", "discovered_count": discovered_count}

    except Exception as e:
        logger.error(f"Discovery agent failed for campaign {campaign_id}: {e}", exc_info=True)
        job.status = "failed"
        job.error_message = str(e)
        db.add(AuditLog(
            action=AuditAction.AGENT_FAILED,
            resource_type="discovery_job",
            resource_id=str(job.id),
            details={"error": str(e)},
        ))
        await db.commit()
        return {"job_id": str(job.id), "status": "failed", "error": str(e)}
