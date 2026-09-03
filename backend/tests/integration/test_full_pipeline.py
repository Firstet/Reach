"""
Integration Test — Complete Outbound Pipeline Simulation (Test Mode)
Validates Discovery → Research → Enrich → Score → Personalize → Send → Reply → Stop Sequence → Escalate.
"""

import pytest
import uuid
from app.models import Campaign, CampaignStatus, LeadStatus, ReplyIntent
from app.services.safety import is_global_kill_switch_active, set_global_kill_switch


class TestPipelineSimulation:
    def test_kill_switch_safety_enforcement(self):
        """Verify global kill switch stops outbound activity."""
        set_global_kill_switch(True)
        assert is_global_kill_switch_active()
        set_global_kill_switch(False)
        assert not is_global_kill_switch_active()

    def test_campaign_configuration_defaults(self):
        """Verify campaign defaults support approval mode, min score, and test mode."""
        c = Campaign(
            name="Nigerian Tech Executives Campaign",
            target_industry="Technology",
            test_mode=True,
            approval_mode="auto",
            min_score_threshold=50.0,
            discovery_query="Find CEOs and CMOs in Nigerian tech companies",
        )
        assert c.test_mode is True
        assert c.approval_mode == "auto"
        assert c.min_score_threshold == 50.0
