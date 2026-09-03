"""Unit tests for AutoAnswer Decision Engine."""

import pytest
from app.services.auto_answer import AutoAnswerEngine, MANDATORY_ESCALATION_PATTERNS


class TestAutoAnswerRules:
    @pytest.mark.asyncio
    async def test_pricing_question_mandatory_escalation(self):
        engine = AutoAnswerEngine(None)
        
        pricing_qs = [
            "How much does it cost?",
            "What are your rates for brand strategy?",
            "Can you give us a discount on retainer fees?",
            "What is your budget requirement?",
        ]
        
        for q in pricing_qs:
            decision = await engine.evaluate_and_answer(q, llm=None)
            assert not decision.can_auto_answer
            assert decision.mandatory_escalation or "Mandatory escalation topic detected" in decision.reason

    @pytest.mark.asyncio
    async def test_guarantee_and_crisis_mandatory_escalation(self):
        engine = AutoAnswerEngine(None)
        
        sensitive_qs = [
            "Can you guarantee results for our launch?",
            "Will you sign this contract and commit to deadline?",
            "Can you handle a PR crisis emergency right now?",
        ]
        
        for q in sensitive_qs:
            decision = await engine.evaluate_and_answer(q, llm=None)
            assert not decision.can_auto_answer
