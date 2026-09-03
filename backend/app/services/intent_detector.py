"""
Buying Intent Signal Detector & Reply Classifier
Detects high-value buying signals in prospect replies, calculates intent scores,
classifies into 13 intent categories, and triggers HOT lead escalations.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field

from app.models import ReplyIntent
from app.providers.base import LLMMessage, LLMProvider

logger = logging.getLogger(__name__)

# Buying intent signal patterns and their score boosts
BUYING_SIGNAL_PATTERNS = [
    (r"\b(schedule a call|book a call|meeting|demo|hop on a call|connect next week|discuss this)\b", 40, "Meeting Request Signal"),
    (r"\b(send a proposal|send details|pricing|quote|cost|retainer|rates)\b", 35, "Proposal / Commercial Signal"),
    (r"\b(planning a rebrand|struggling with|looking for a partner|need help with|rebranding|communications partner)\b", 35, "Active Strategic Need Signal"),
    (r"\b(sounds interesting|like to know more|tell me more|curious|how does this work)\b", 25, "Interest / Curiosity Signal"),
    (r"\b(working with|our team|current agency|existing marketing)\b", 20, "Capability Fit Signal"),
]


@dataclass
class IntentAnalysis:
    intent: ReplyIntent
    confidence: float
    intent_score: float  # 0 to 100
    detected_signals: list[str] = field(default_factory=list)
    is_high_intent: bool = False
    summary: str = ""
    suggested_action: str = ""


class IntentDetector:
    """Detects buying signals and classifies prospect reply intent."""

    def analyze_reply(self, text: str, llm: LLMProvider | None = None) -> IntentAnalysis:
        """Run pattern detection + LLM classification to produce IntentAnalysis."""
        clean_text = text.lower().strip()

        # 1. Regex Buying Signal Detection
        boost_score = 0.0
        detected_signals = []
        for pattern, score_add, signal_name in BUYING_SIGNAL_PATTERNS:
            if re.search(pattern, clean_text):
                boost_score += score_add
                detected_signals.append(signal_name)

        # 2. Check explicit unsubscribes / negative signals
        if any(term in clean_text for term in ["unsubscribe", "opt out", "stop emailing", "remove me", "do not contact"]):
            return IntentAnalysis(
                intent=ReplyIntent.UNSUBSCRIBE,
                confidence=1.0,
                intent_score=0.0,
                detected_signals=["Unsubscribe Requested"],
                is_high_intent=False,
                summary="Prospect requested to unsubscribe.",
                suggested_action="Stop all communications immediately.",
            )

        if any(term in clean_text for term in ["not interested", "no thanks", "pass", "remove", "don't need"]):
            return IntentAnalysis(
                intent=ReplyIntent.NOT_INTERESTED,
                confidence=0.9,
                intent_score=10.0,
                detected_signals=["Not Interested"],
                is_high_intent=False,
                summary="Prospect indicated lack of interest.",
                suggested_action="Archive lead or move to Nurture.",
            )

        # Base intent score calculation
        base_score = min(50.0 + boost_score, 100.0)
        is_high = base_score >= 75.0 or len(detected_signals) >= 2 or "Meeting Request Signal" in detected_signals

        # Default classification mapping
        if "Meeting Request Signal" in detected_signals:
            intent = ReplyIntent.MEETING_REQUEST
        elif "Proposal / Commercial Signal" in detected_signals:
            intent = ReplyIntent.PRICING
        elif is_high:
            intent = ReplyIntent.HIGH_INTENT
        elif "Interest / Curiosity Signal" in detected_signals:
            intent = ReplyIntent.CURIOUS
        elif "?" in text:
            intent = ReplyIntent.QUESTION
        else:
            intent = ReplyIntent.INTERESTED if base_score >= 60 else ReplyIntent.POLITE_RESPONSE

        return IntentAnalysis(
            intent=intent,
            confidence=0.85 if detected_signals else 0.70,
            intent_score=base_score,
            detected_signals=detected_signals,
            is_high_intent=is_high,
            summary=f"Reply received with {len(detected_signals)} buying signals detected.",
            suggested_action="Take over conversation in Dashboard" if is_high else "Review response",
        )

    async def analyze_with_llm(self, text: str, llm: LLMProvider) -> IntentAnalysis:
        """Deep LLM classification coupled with signal detection."""
        base_analysis = self.analyze_reply(text)

        system_prompt = (
            "You are an AI Sales Intelligence Classifier for Rayven Strategic Communications.\n"
            "Classify the prospect reply into exactly ONE intent key:\n"
            "NOT_INTERESTED, POLITE_RESPONSE, QUESTION, CURIOUS, INTERESTED, HIGH_INTENT, MEETING_REQUEST, PRICING, NEGOTIATION, COMPLAINT, UNSUBSCRIBE, DO_NOT_CONTACT, UNKNOWN.\n"
            "Calculate intent_score (0-100) based on commercial buying signals. Output JSON only."
        )

        user_prompt = f"""
Prospect Reply:
"{text}"

Detected Pattern Signals: {base_analysis.detected_signals}

Return JSON object:
- intent: string (one of the 13 keys listed above)
- confidence: float 0.0 to 1.0
- intent_score: float 0 to 100
- detected_signals: list of buying signals identified in text
- is_high_intent: boolean (true if intent_score >= 75 or asking for meeting/proposal/rebrand help)
- summary: 1-sentence summary of what the prospect said and their core underlying need
- suggested_action: recommended human operator action item

Do NOT include markdown wrappers.
"""

        try:
            raw = await llm.complete(
                [LLMMessage(role="system", content=system_prompt), LLMMessage(role="user", content=user_prompt)],
                temperature=0.1,
            )
            clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            data = json.loads(clean)

            intent_str = data.get("intent", "INTERESTED").upper()
            try:
                intent_enum = ReplyIntent[intent_str]
            except KeyError:
                intent_enum = base_analysis.intent

            score = float(data.get("intent_score", base_analysis.intent_score))
            is_high = bool(data.get("is_high_intent", score >= 75.0))

            return IntentAnalysis(
                intent=intent_enum,
                confidence=float(data.get("confidence", 0.85)),
                intent_score=score,
                detected_signals=data.get("detected_signals", base_analysis.detected_signals),
                is_high_intent=is_high,
                summary=data.get("summary", base_analysis.summary),
                suggested_action=data.get("suggested_action", base_analysis.suggested_action),
            )
        except Exception as e:
            logger.warning(f"LLM intent classification error: {e}, using heuristic analysis")
            return base_analysis
