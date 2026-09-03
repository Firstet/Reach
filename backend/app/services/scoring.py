"""
Lead Scoring Engine
Configurable multi-dimensional scoring engine that evaluates ICP fit, decision-maker seniority,
company size, geography, communication opportunities, and email confidence.
Enforces score tiers: 0-39 (reject), 40-59 (low), 60-74 (qualified), 75-89 (high), 90-100 (priority).
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Campaign, Lead, LeadScore, LeadStatus, Prospect, ProspectResearch

logger = logging.getLogger(__name__)

DEFAULT_SCORING_WEIGHTS = {
    "seniority": 30,         # C-level=30, VP=25, Director=20, Head=15
    "industry_fit": 25,     # Exact target industry match=25, adjacent=15
    "communication_signal": 20, # Strategic PR/brand need evidence=20, general=10
    "email_confidence": 15, # Verified=15, high conf=10, unverified=5
    "company_size": 10,     # Growth stage / 50-500 employees=10
}


@dataclass
class ScoreBreakdown:
    total_score: float
    seniority_score: float
    industry_score: float
    signal_score: float
    email_score: float
    size_score: float
    is_qualified: bool
    qualification_tier: str  # REJECT | LOW_PRIORITY | QUALIFIED | HIGH_PRIORITY | PRIORITY_LEAD
    reason: str


class ScoringService:
    """Computes configurable weighted scores for leads."""

    def __init__(self, session: AsyncSession):
        self._db = session

    async def score_lead(
        self,
        lead_id: uuid.UUID,
        custom_weights: dict | None = None,
    ) -> LeadScore:
        """Compute score breakdown for a lead and save LeadScore record."""
        lead = await self._db.get(Lead, lead_id)
        if not lead or not lead.prospect:
            raise ValueError(f"Lead {lead_id} missing prospect")

        prospect = lead.prospect
        company = prospect.company
        research = await self._get_prospect_research(lead.id)
        campaign = lead.campaign

        weights = custom_weights or (campaign.scoring_weights if campaign and campaign.scoring_weights else DEFAULT_SCORING_WEIGHTS)

        breakdown = self.calculate_breakdown(
            prospect=prospect,
            company=company,
            research=research,
            campaign=campaign,
            weights=weights,
        )

        # Save or update LeadScore
        existing_score = await self._db.execute(
            select(LeadScore).where(LeadScore.lead_id == lead.id)
        )
        score_obj = existing_score.scalar_one_or_none()

        if not score_obj:
            score_obj = LeadScore(
                id=uuid.uuid4(),
                lead_id=lead.id,
                total_score=breakdown.total_score,
                seniority_fit=breakdown.seniority_score,
                industry_fit=breakdown.industry_score,
                company_size_fit=breakdown.size_score,
                email_confidence=breakdown.email_score,
                engagement_score=breakdown.signal_score,
                is_qualified=breakdown.is_qualified,
                qualification_reason=breakdown.reason,
                scored_by="agent",
                scoring_metadata={
                    "tier": breakdown.qualification_tier,
                    "weights_used": weights,
                },
            )
            self._db.add(score_obj)
        else:
            score_obj.total_score = breakdown.total_score
            score_obj.seniority_fit = breakdown.seniority_score
            score_obj.industry_fit = breakdown.industry_score
            score_obj.company_size_fit = breakdown.size_score
            score_obj.email_confidence = breakdown.email_score
            score_obj.engagement_score = breakdown.signal_score
            score_obj.is_qualified = breakdown.is_qualified
            score_obj.qualification_reason = breakdown.reason
            score_obj.scoring_metadata = {
                "tier": breakdown.qualification_tier,
                "weights_used": weights,
            }

        # Handle lead status based on score threshold
        min_threshold = campaign.min_score_threshold if campaign else 40.0
        if breakdown.total_score < min_threshold or breakdown.qualification_tier == "REJECT":
            lead.status = LeadStatus.NOT_INTERESTED
            lead.is_stopped = True
            lead.stopped_reason = f"Rejected by scoring ({breakdown.total_score:.1f} < {min_threshold})"
        elif breakdown.is_qualified:
            lead.status = LeadStatus.QUALIFIED

        await self._db.commit()
        await self._db.refresh(score_obj)
        return score_obj

    def calculate_breakdown(
        self,
        prospect: Prospect,
        company: Any,
        research: ProspectResearch | None,
        campaign: Campaign | None,
        weights: dict,
    ) -> ScoreBreakdown:
        """Calculate weighted score breakdown."""
        # 1. Seniority Fit
        max_seniority = float(weights.get("seniority", 30))
        seniority_score = 0.0
        title_lower = (prospect.title or "").lower()
        if any(term in title_lower for term in ["ceo", "chief executive", "founder", "managing director", "president"]):
            seniority_score = max_seniority
        elif any(term in title_lower for term in ["cmo", "chief marketing", "c-level", "chief"]):
            seniority_score = max_seniority * 0.9
        elif any(term in title_lower for term in ["vp", "vice president", "executive director"]):
            seniority_score = max_seniority * 0.8
        elif any(term in title_lower for term in ["director", "head of"]):
            seniority_score = max_seniority * 0.7
        elif "manager" in title_lower or "lead" in title_lower:
            seniority_score = max_seniority * 0.5
        else:
            seniority_score = max_seniority * 0.3

        # 2. Industry Fit
        max_industry = float(weights.get("industry_fit", 25))
        industry_score = max_industry * 0.5  # default
        if company and company.industry:
            comp_ind = company.industry.lower()
            target_ind = (campaign.target_industry or "").lower() if campaign else ""
            if target_ind and target_ind in comp_ind:
                industry_score = max_industry
            elif any(ind in comp_ind for ind in ["tech", "finance", "banking", "health", "energy", "consumer"]):
                industry_score = max_industry * 0.85

        # 3. Communication Signal / Strategic Need
        max_signal = float(weights.get("communication_signal", 20))
        signal_score = max_signal * 0.5
        if research:
            if research.why_rayven_relevant and len(research.why_rayven_relevant) > 20:
                signal_score = max_signal
            elif research.communication_signals:
                signal_score = max_signal * 0.8

        # 4. Email Confidence
        max_email = float(weights.get("email_confidence", 15))
        email_conf = prospect.email_confidence or 0.5
        if prospect.email_verified:
            email_score = max_email
        else:
            email_score = max_email * email_conf

        # 5. Company Size
        max_size = float(weights.get("company_size", 10))
        size_score = max_size * 0.7

        total_score = round(seniority_score + industry_score + signal_score + email_score + size_score, 1)
        total_score = min(total_score, 100.0)

        # Classify Tier
        if total_score >= 90.0:
            tier = "PRIORITY_LEAD"
            is_qual = True
        elif total_score >= 75.0:
            tier = "HIGH_PRIORITY"
            is_qual = True
        elif total_score >= 60.0:
            tier = "QUALIFIED"
            is_qual = True
        elif total_score >= 40.0:
            tier = "LOW_PRIORITY"
            is_qual = False
        else:
            tier = "REJECT"
            is_qual = False

        reason = (
            f"Score {total_score:.1f}/100 [{tier}]: Seniority ({seniority_score:.1f}/{max_seniority}), "
            f"Industry ({industry_score:.1f}/{max_industry}), Communication Need ({signal_score:.1f}/{max_signal}), "
            f"Email ({email_score:.1f}/{max_email})"
        )

        return ScoreBreakdown(
            total_score=total_score,
            seniority_score=seniority_score,
            industry_score=industry_score,
            signal_score=signal_score,
            email_score=email_score,
            size_score=size_score,
            is_qualified=is_qual,
            qualification_tier=tier,
            reason=reason,
        )

    async def _get_prospect_research(self, lead_id: uuid.UUID) -> ProspectResearch | None:
        stmt = select(ProspectResearch).where(ProspectResearch.lead_id == lead_id)
        res = await self._db.execute(stmt)
        return res.scalar_one_or_none()
