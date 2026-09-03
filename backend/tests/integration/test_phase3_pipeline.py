"""Integration test for Phase 3 Conversation, Copilot, & Handoff Pipeline."""

import pytest
from app.models import CRMStage, ConversationStatus, ReplyIntent
from app.services.intent_detector import IntentDetector


class TestPhase3Integration:
    def test_crm_stage_enum_alignment(self):
        assert CRMStage.DISCOVERED.value == "discovered"
        assert CRMStage.HOT.value == "hot"
        assert CRMStage.MEETING.value == "meeting"
        assert CRMStage.WON.value == "won"

    def test_intent_detection_to_crm_stage_mapping(self):
        detector = IntentDetector()
        reply_text = "We need help with brand positioning. Can we schedule a call?"
        analysis = detector.analyze_reply(reply_text)
        
        assert analysis.is_high_intent
        assert analysis.intent_score >= 80.0
