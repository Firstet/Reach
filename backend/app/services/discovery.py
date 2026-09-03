"""
Lead Discovery Service
Translates natural language campaign instructions into structured search criteria,
queries web search / LinkedIn / CSV imports, extracts companies and decision-makers,
deduplicates, and enrolls discovered prospects as Leads.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Company, Lead, LeadStatus, Prospect
from app.providers.base import LLMMessage, LLMProvider, SearchProvider
from app.services.safety import SafetyService

logger = logging.getLogger(__name__)


@dataclass
class StructuredSearchCriteria:
    target_roles: list[str] = field(default_factory=list)
    target_industries: list[str] = field(default_factory=list)
    target_locations: list[str] = field(default_factory=list)
    company_size: str = ""
    value_drivers: list[str] = field(default_factory=list)
    search_queries: list[str] = field(default_factory=list)


@dataclass
class DiscoveredCompany:
    name: str
    domain: str = ""
    website: str = ""
    industry: str = ""
    country: str = ""
    city: str = ""
    description: str = ""
    source: str = "web_search"


@dataclass
class DiscoveredProspect:
    first_name: str
    last_name: str
    title: str
    company_name: str
    company_domain: str = ""
    linkedin_url: str = ""
    location: str = ""
    email: str = ""
    confidence: float = 0.5
    source: str = "web_search"


class DiscoveryService:
    """Core logic for translating instructions, searching web/LinkedIn, and creating entities."""

    def __init__(self, session: AsyncSession):
        self._db = session
        self._safety = SafetyService(session)

    async def parse_campaign_query(self, query_text: str, llm: LLMProvider) -> StructuredSearchCriteria:
        """Use LLM to translate natural language instruction into structured search criteria."""
        system_prompt = (
            "You are an expert sales development analyst. Analyze the user's campaign targeting instructions "
            "and extract structured search criteria into valid JSON only."
        )
        user_prompt = f"""
Campaign instruction:
"{query_text}"

Extract JSON with keys:
- target_roles: list of job titles (e.g. ["CEO", "CMO", "Marketing Director"])
- target_industries: list of industries (e.g. ["Technology", "Finance"])
- target_locations: list of countries or cities (e.g. ["Nigeria", "Africa", "Lagos"])
- company_size: string if specified
- value_drivers: list of strategic communication needs or signals
- search_queries: array of 4-6 specific Google search query strings to find matching companies and leaders in these sectors/locations (e.g. 'site:linkedin.com/in "CMO" "Nigeria" "Technology"')

Respond ONLY with raw valid JSON, no markdown wrappers.
"""
        try:
            raw = await llm.complete(
                [LLMMessage(role="system", content=system_prompt), LLMMessage(role="user", content=user_prompt)],
                temperature=0.2,
            )
            clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            data = json.loads(clean)
            return StructuredSearchCriteria(
                target_roles=data.get("target_roles", []),
                target_industries=data.get("target_industries", []),
                target_locations=data.get("target_locations", []),
                company_size=data.get("company_size", ""),
                value_drivers=data.get("value_drivers", []),
                search_queries=data.get("search_queries", []),
            )
        except Exception as e:
            logger.error(f"Failed to parse campaign query via LLM: {e}")
            # Fallback heuristic criteria
            return StructuredSearchCriteria(
                target_roles=["CEO", "Founder", "CMO", "Marketing Director", "Communications Director"],
                target_industries=["Technology", "Finance", "Healthcare"],
                target_locations=["Nigeria"],
                search_queries=[f"{query_text} company leadership CEO CMO Nigeria"],
            )

    async def discover_via_search(
        self,
        criteria: StructuredSearchCriteria,
        search_provider: SearchProvider,
        max_results: int = 20,
    ) -> list[DiscoveredProspect]:
        """Query web search provider for prospects and company signals."""
        discovered: list[DiscoveredProspect] = []
        if not search_provider:
            return discovered

        for q in criteria.search_queries[:4]:
            try:
                results = await search_provider.search(q, num_results=10)
                for res in results:
                    prospect = self._parse_search_result_to_prospect(res.title, res.snippet, res.url)
                    if prospect:
                        discovered.append(prospect)
            except Exception as e:
                logger.error(f"Search query '{q}' failed: {e}")

        return discovered[:max_results]

    def _parse_search_result_to_prospect(self, title: str, snippet: str, url: str) -> DiscoveredProspect | None:
        """Extract structured prospect data from web search snippet."""
        # Check if LinkedIn profile result
        if "linkedin.com/in/" in url:
            # Pattern: Name - Title - Company | LinkedIn
            clean_title = re.sub(r"\s*\|\s*LinkedIn.*$", "", title)
            parts = [p.strip() for p in clean_title.split("-") if p.strip()]
            if len(parts) >= 2:
                full_name = parts[0]
                name_parts = full_name.split(maxsplit=1)
                first_name = name_parts[0]
                last_name = name_parts[1] if len(name_parts) > 1 else ""
                role_title = parts[1]
                company_name = parts[2] if len(parts) > 2 else ""

                return DiscoveredProspect(
                    first_name=first_name,
                    last_name=last_name,
                    title=role_title,
                    company_name=company_name,
                    linkedin_url=url,
                    confidence=0.75,
                    source="google_linkedin",
                )

        # General web result parsing
        name_match = re.search(r"([A-Z][a-z]+ [A-Z][a-z]+),?\s+(CEO|Founder|CMO|Director|Managing Director|Head of Marketing)", title + " " + snippet)
        if name_match:
            full_name = name_match.group(1)
            role = name_match.group(2)
            parts = full_name.split(maxsplit=1)
            return DiscoveredProspect(
                first_name=parts[0],
                last_name=parts[1] if len(parts) > 1 else "",
                title=role,
                company_name="",
                confidence=0.5,
                source="web_search",
            )

        return None

    async def ingest_csv_prospects(
        self,
        rows: list[dict[str, Any]],
        campaign_id: uuid.UUID,
    ) -> list[uuid.UUID]:
        """Bulk import prospects from CSV data."""
        created_lead_ids = []
        for row in rows:
            first_name = (row.get("first_name") or row.get("FirstName") or "").strip()
            last_name = (row.get("last_name") or row.get("LastName") or "").strip()
            email = (row.get("email") or row.get("Email") or "").strip().lower()
            company_name = (row.get("company") or row.get("Company") or "").strip()
            title = (row.get("title") or row.get("Title") or "").strip()

            if not first_name or not company_name:
                continue

            # Get or create company
            company = await self._get_or_create_company(
                name=company_name,
                domain=(row.get("domain") or row.get("Domain") or "").strip().lower(),
                industry=(row.get("industry") or row.get("Industry") or "").strip(),
            )

            # Get or create prospect
            prospect = await self._get_or_create_prospect(
                company_id=company.id,
                first_name=first_name,
                last_name=last_name,
                email=email if email else None,
                title=title,
                linkedin_url=(row.get("linkedin") or row.get("LinkedIn") or "").strip(),
                source="csv_import",
            )

            # Enroll lead
            lead = await self._enroll_lead(prospect.id, campaign_id, source="csv_import")
            if lead:
                created_lead_ids.append(lead.id)

        await self._db.commit()
        return created_lead_ids

    async def _get_or_create_company(self, name: str, domain: str = "", industry: str = "") -> Company:
        """Find company by domain or name, create if missing."""
        clean_domain = domain.lower().strip() if domain else None
        if clean_domain:
            stmt = select(Company).where(Company.domain == clean_domain)
            res = await self._db.execute(stmt)
            existing = res.scalar_one_or_none()
            if existing:
                return existing

        stmt = select(Company).where(Company.name.ilike(name.strip()))
        res = await self._db.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            return existing

        comp = Company(
            id=uuid.uuid4(),
            name=name.strip(),
            domain=clean_domain,
            industry=industry or None,
            source="discovery",
        )
        self._db.add(comp)
        await self._db.flush()
        return comp

    async def _get_or_create_prospect(
        self,
        company_id: uuid.UUID | None,
        first_name: str,
        last_name: str,
        email: str | None = None,
        title: str | None = None,
        linkedin_url: str | None = None,
        source: str = "discovery",
    ) -> Prospect:
        """Deduplicate prospect by email or name+company, create if missing."""
        if email:
            stmt = select(Prospect).where(Prospect.email == email.lower().strip())
            res = await self._db.execute(stmt)
            existing = res.scalar_one_or_none()
            if existing:
                return existing

        if company_id:
            stmt = select(Prospect).where(
                Prospect.company_id == company_id,
                Prospect.first_name.ilike(first_name.strip()),
                Prospect.last_name.ilike(last_name.strip()),
            )
            res = await self._db.execute(stmt)
            existing = res.scalar_one_or_none()
            if existing:
                return existing

        prospect = Prospect(
            id=uuid.uuid4(),
            company_id=company_id,
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            email=email.lower().strip() if email else None,
            title=title,
            linkedin_url=linkedin_url or None,
            source=source,
        )
        self._db.add(prospect)
        await self._db.flush()
        return prospect

    async def _enroll_lead(
        self,
        prospect_id: uuid.UUID,
        campaign_id: uuid.UUID,
        source: str = "discovery",
    ) -> Lead | None:
        """Enroll prospect into campaign if not already enrolled."""
        if await self._safety.is_duplicate_lead(prospect_id, campaign_id):
            logger.info(f"Prospect {prospect_id} already enrolled in campaign {campaign_id}")
            return None

        lead = Lead(
            id=uuid.uuid4(),
            prospect_id=prospect_id,
            campaign_id=campaign_id,
            status=LeadStatus.DISCOVERED,
            discovery_source=source,
        )
        self._db.add(lead)
        await self._db.flush()
        return lead
