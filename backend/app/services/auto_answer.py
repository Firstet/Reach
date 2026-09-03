"""
Automatic Answer & Escalation Decision Engine
Determines whether a prospect's inquiry can be answered automatically with high KB confidence,
or MUST be escalated to a human operator due to sensitive topics (pricing, guarantees, contracts, crisis).
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.providers.base import LLMMessage, LLMProvider
from app.services.knowledge_agent import KnowledgeSearchResult, RayvenKnowledgeAgent

logger = logging.getLogger(__name__)

# Mandatory escalation regex patterns (pricing, guarantees, contracts, legal, crisis)
MANDATORY_ESCALATION_PATTERNS = [
    r"\b(how much|cost|pricing|price|rates|quote|fee|fees|budget|retainer|discount)\b",
    r"\b(guarantee|guaranteed|promise|commit|deadline|sla|contract|sign contract|legal)\b",
    r"\b(crisis|emergency|scandal|lawsuit|investigation|pr disaster)\b",
]


@dataclass
class AutoAnswerDecision:
    can_auto_answer: bool
    reason: str
    suggested_answer: str = ""
    citations: list[str] = None
    confidence: float = 0.0
    mandatory_escalation: bool = False


class AutoAnswerEngine:
    """Evaluates prospect inquiries and executes KB-backed auto-replies or escalates."""

    def __init__(self, session: AsyncSession):
        self._db = session
        self._kb_agent = RayvenKnowledgeAgent(session)

    async def evaluate_and_answer(
        self,
        question_text: str,
        llm: LLMProvider | None = None,
    ) -> AutoAnswerDecision:
        """
        Evaluate if a prospect question can be answered automatically.
        Enforces mandatory escalation topics (pricing, contracts, guarantees, crisis).
        """
        clean_text = question_text.lower().strip()

        # 1. Check Mandatory Escalation Topic Regex
        for pattern in MANDATORY_ESCALATION_PATTERNS:
            if re.search(pattern, clean_text):
                match_term = re.search(pattern, clean_text).group(0)
                logger.info(f"Mandatory escalation triggered by topic match: '{match_term}' in '{question_text}'")
                return AutoAnswerDecision(
                    can_auto_answer=False,
                    reason=f"Mandatory escalation topic detected: '{match_term}'",
                    mandatory_escalation=True,
                    confidence=1.0,
                )

        # 2. Query Knowledge Base with Source Citations
        kb_results = []
        if llm:
            try:
                kb_results = await self._kb_agent.search_with_citations(
                    llm=llm, query=question_text, k=4, threshold=0.70
                )
            except Exception as e:
                logger.warning(f"KB search failed in AutoAnswerEngine: {e}")

        # Check if KB confidence is sufficient
        highest_similarity = max([r.similarity for r in kb_results], default=0.0) if kb_results else 0.0
        if highest_similarity < 0.72 or not kb_results:
            return AutoAnswerDecision(
                can_auto_answer=False,
                reason=f"Insufficient Knowledge Base evidence (max similarity: {highest_similarity:.2f})",
                confidence=highest_similarity,
            )

        # 3. LLM Evaluation & Auto-Reply Generation
        kb_context_str = "\n".join([f"{r.citation}\n{r.content}" for r in kb_results])

        system_prompt = (
            "You are the AI Business Development Assistant at Rayven Strategic Communications (RayvenSC).\n"
            "Evaluate whether the prospect's question can be answered COMPLETELY and CONFIDENTLY using ONLY the provided Knowledge Base context.\n\n"
            "STRICT RULES:\n"
            "1. If the question asks for custom pricing, quotes, guaranteed outcomes, contractual commitments, or crisis advice -> DO NOT answer automatically. Set can_auto_answer=false.\n"
            "2. If the question asks about Rayven's services, framework (Context Intelligence, Narrative Architecture, Strategic Deployment, Outcome Measurement), methodology, team, or location -> Answer concisely, authoritatively, and warmly.\n"
            "3. Communicate like a senior strategic consultant: concise (under 100 words), strategic, consultative.\n"
            "4. NEVER invent facts. Ground every claim in the KB evidence.\n"
            "5. Include citations at the end of the answer.\n"
            "Output JSON only."
        )

        user_prompt = f"""
Prospect Inquiry:
"{question_text}"

Rayven Knowledge Base Context:
{kb_context_str}

Respond with raw JSON object:
- can_auto_answer: boolean (true only if routine question answered with 100% confidence from context)
- reason: string explaining decision
- answer: string (the generated response text if can_auto_answer is true)
- confidence: float between 0.0 and 1.0

Do NOT include markdown syntax around JSON.
"""

        if not llm:
            # Fallback if no LLM
            citations = [r.citation for r in kb_results]
            return AutoAnswerDecision(
                can_auto_answer=True,
                reason="Routine question matched KB context",
                suggested_answer=f"{kb_results[0].content}\n\n{' '.join(citations)}",
                citations=citations,
                confidence=0.85,
            )

        try:
            raw = await llm.complete(
                [LLMMessage(role="system", content=system_prompt), LLMMessage(role="user", content=user_prompt)],
                temperature=0.2,
            )
            clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            data = json.loads(clean)

            can_ans = bool(data.get("can_auto_answer", False))
            conf = float(data.get("confidence", 0.8))

            if can_ans and conf >= 0.80:
                citations = [r.citation for r in kb_results[:2]]
                ans_text = data.get("answer", "")
                return AutoAnswerDecision(
                    can_auto_answer=True,
                    reason=data.get("reason", "Answered confidently from Rayven KB"),
                    suggested_answer=ans_text,
                    citations=citations,
                    confidence=conf,
                )
            else:
                return AutoAnswerDecision(
                    can_auto_answer=False,
                    reason=data.get("reason", "Inquiry requires human strategic review"),
                    confidence=conf,
                )

        except Exception as e:
            logger.error(f"AutoAnswer evaluation error: {e}")
            return AutoAnswerDecision(
                can_auto_answer=False,
                reason=f"Evaluation error: {e}",
                confidence=0.0,
            )
