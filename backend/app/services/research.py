"""
AI Research Service
Gathers factual web data for companies and decision-makers, conducts deep LLM analysis,
distinguishes evidence from inference, and generates structured ProspectResearch records.
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Company, Lead, LeadStatus, Prospect, ProspectResearch
from app.providers.base import LLMMessage, LLMProvider, SearchProvider

logger = logging.getLogger(__name__)


@dataclass
class ProspectIntelligence:
    company_name: str
    prospect_name: str
    role: str
    industry: str
    business_context: str
    recent_developments: str
    communication_signals: str
    potential_challenge: str
    potential_opportunity: str
    why_rayven_relevant: str
    evidence: str
    source_urls: list[str] = field(default_factory=list)
    confidence: float = 0.8


class ResearchService:
    """Performs deep research on a lead's company and prospect background."""

    def __init__(self, session: AsyncSession):
        self._db = session

    async def research_lead(
        self,
        lead_id: uuid.UUID,
        llm: LLMProvider,
        search: SearchProvider | None = None,
    ) -> ProspectResearch:
        """Conduct research on a lead and save/update ProspectResearch."""
        lead = await self._db.get(Lead, lead_id)
        if not lead:
            raise ValueError(f"Lead {lead_id} not found")

        prospect = lead.prospect
        company = prospect.company if prospect else None

        if not prospect or not company:
            raise ValueError(f"Lead {lead_id} missing prospect or company")

        # 1. Gather web search evidence if search provider available
        search_snippets = []
        source_urls = []
        if search and not lead.is_test:
            queries = [
                f"{company.name} {company.industry or ''} news developments",
                f"{prospect.full_name} {company.name} {prospect.title or ''}",
                f"{company.name} communications marketing brand strategy",
            ]
            for q in queries:
                try:
                    res = await search.search(q, num_results=3)
                    for item in res:
                        search_snippets.append(f"Source ({item.url}): {item.snippet}")
                        if item.url not in source_urls:
                            source_urls.append(item.url)
                except Exception as e:
                    logger.warning(f"Search query '{q}' failed: {e}")

        search_context_text = "\n".join(search_snippets) if search_snippets else "No live web search results available."

        # 2. LLM Analysis — Prompt engineered for factual rigor and RayvenSC positioning
        system_prompt = (
            "You are a senior strategic communications consultant at Rayven Strategic Communications (RayvenSC). "
            "You analyze corporate contexts to identify genuine communication gaps, brand architecture needs, "
            "and reputation/growth opportunities. You strictly distinguish empirical evidence from inference. "
            "NEVER invent or fabricate facts. Output JSON only."
        )

        user_prompt = f"""
Company: {company.name}
Domain: {company.domain or 'Unknown'}
Industry: {company.industry or 'Unknown'}
Description: {company.description or 'None provided'}
Prospect: {prospect.full_name}
Title: {prospect.title or 'Unknown'}
Location: {prospect.location or 'Unknown'}

Web Evidence:
{search_context_text}

Perform structured research analysis. Return a raw JSON object with keys:
- company_context: factual 2-sentence summary of company positioning and market
- recent_developments: verified public developments, news, launches, or regulatory events (state 'None verified' if unconfirmed)
- communication_signals: evidence of brand, PR, corporate affairs, or marketing activity/gaps
- potential_challenge: primary narrative, stakeholder, or market understanding challenge facing this organisation
- potential_opportunity: how narrative architecture, strategic communications, or digital growth could create value
- why_rayven_relevant: specific reason RayvenSC (context intelligence, narrative architecture, outcome measurement) is relevant
- evidence: bulleted summary of verified empirical facts vs logical inferences
- confidence: float score between 0.0 and 1.0 (based on quality of evidence)

Do NOT include markdown syntax around the JSON.
"""

        try:
            raw = await llm.complete(
                [LLMMessage(role="system", content=system_prompt), LLMMessage(role="user", content=user_prompt)],
                temperature=0.3,
            )
            clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            data = json.loads(clean)
        except Exception as e:
            logger.error(f"LLM research analysis failed: {e}")
            data = {
                "company_context": f"{company.name} operates in the {company.industry or 'broader market'} sector.",
                "recent_developments": "No verified recent developments.",
                "communication_signals": f"Leadership title: {prospect.title}.",
                "potential_challenge": "Aligning corporate messaging with stakeholder expectations.",
                "potential_opportunity": "Building a structured narrative architecture for sustained market trust.",
                "why_rayven_relevant": "RayvenSC provides the Context Intelligence and Narrative Architecture needed for strategic positioning.",
                "evidence": f"Empirical: Title is {prospect.title} at {company.name}.",
                "confidence": 0.6,
            }

        # 3. Create or update ProspectResearch record
        existing_res = await self._db.execute(
            select(ProspectResearch).where(ProspectResearch.lead_id == lead.id)
        )
        research = existing_res.scalar_one_or_none()

        if not research:
            research = ProspectResearch(
                id=uuid.uuid4(),
                lead_id=lead.id,
                company_context=data.get("company_context"),
                recent_developments=data.get("recent_developments"),
                communication_signals=data.get("communication_signals"),
                potential_challenge=data.get("potential_challenge"),
                potential_opportunity=data.get("potential_opportunity"),
                why_rayven_relevant=data.get("why_rayven_relevant"),
                evidence=data.get("evidence"),
                source_urls=source_urls,
                confidence=float(data.get("confidence", 0.8)),
                raw_intelligence=data,
            )
            self._db.add(research)
        else:
            research.company_context = data.get("company_context")
            research.recent_developments = data.get("recent_developments")
            research.communication_signals = data.get("communication_signals")
            research.potential_challenge = data.get("potential_challenge")
            research.potential_opportunity = data.get("potential_opportunity")
            research.why_rayven_relevant = data.get("why_rayven_relevant")
            research.evidence = data.get("evidence")
            research.source_urls = source_urls
            research.confidence = float(data.get("confidence", 0.8))
            research.raw_intelligence = data

        # Also update company research summary
        company.research_summary = data.get("company_context")
        prospect.research_summary = f"{data.get('potential_challenge')} | {data.get('why_rayven_relevant')}"

        # Update lead status
        if lead.status == LeadStatus.DISCOVERED or lead.status == LeadStatus.NEW:
            lead.status = LeadStatus.RESEARCHED

        await self._db.commit()
        await self._db.refresh(research)
        return research
