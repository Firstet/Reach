"""Unit tests for IntentDetector & Buying Signal Detection."""

import pytest
from app.models import ReplyIntent
from app.services.intent_detector import IntentDetector


class TestIntentDetector:
    def test_buying_signal_detection(self):
        detector = IntentDetector()
        
        reply_text = "This sounds interesting. We are planning a rebrand and would like to schedule a call to discuss."
        analysis = detector.analyze_reply(reply_text)
        
        assert analysis.is_high_intent
        assert analysis.intent_score >= 75.0
        assert "Meeting Request Signal" in analysis.detected_signals
        assert "Active Strategic Need Signal" in analysis.detected_signals
        assert analysis.intent in (ReplyIntent.MEETING_REQUEST, ReplyIntent.HIGH_INTENT)

    def test_unsubscribe_intent(self):
        detector = IntentDetector()
        
        reply_text = "Please unsubscribe me from your emails."
        analysis = detector.analyze_reply(reply_text)
        
        assert analysis.intent == ReplyIntent.UNSUBSCRIBE
        assert analysis.intent_score == 0.0
        assert not analysis.is_high_intent
