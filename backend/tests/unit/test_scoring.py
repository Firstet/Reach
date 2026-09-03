"""Unit tests for Lead Scoring Engine."""

import pytest
from app.models import Campaign, Prospect, ProspectResearch
from app.services.scoring import ScoringService, DEFAULT_SCORING_WEIGHTS


class TestScoringEngine:
    def test_ceo_scoring_priority_tier(self):
        service = ScoringService(None)
        prospect = Prospect(first_name="Amina", last_name="Bello", title="Chief Executive Officer", email_confidence=0.9, email_verified=True)
        company = type("Company", (), {"industry": "Technology"})()
        research = ProspectResearch(
            why_rayven_relevant="High strategic need for narrative architecture during upcoming expansion.",
            communication_signals="Active PR campaigns",
        )
        campaign = Campaign(target_industry="Technology")

        breakdown = service.calculate_breakdown(
            prospect=prospect,
            company=company,
            research=research,
            campaign=campaign,
            weights=DEFAULT_SCORING_WEIGHTS,
        )

        assert breakdown.total_score >= 90.0
        assert breakdown.is_qualified
        assert breakdown.qualification_tier == "PRIORITY_LEAD"

    def test_low_seniority_rejection(self):
        service = ScoringService(None)
        prospect = Prospect(first_name="John", last_name="Doe", title="Intern", email_confidence=0.2, email_verified=False)
        company = type("Company", (), {"industry": "Agriculture"})()
        campaign = Campaign(target_industry="Finance")

        breakdown = service.calculate_breakdown(
            prospect=prospect,
            company=company,
            research=None,
            campaign=campaign,
            weights=DEFAULT_SCORING_WEIGHTS,
        )

        assert breakdown.total_score < 60.0
        assert not breakdown.is_qualified
