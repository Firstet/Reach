"""
AI Copilot Assistant Service
Generates private assistant recommendations, response variations, objection handling,
meeting preparation questions, and relevant Rayven framework service suggestions for human operators.
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Conversation, Lead, Message, MessageDirection, ProspectResearch
from app.providers.base import LLMMessage, LLMProvider
from app.services.knowledge_agent import RayvenKnowledgeAgent

logger = logging.getLogger(__name__)


@dataclass
class CopilotRecommendations:
    conversation_summary: str
    recommended_replies: list[dict[str, str]]  # list of {"tone": "Consultative", "subject": "...", "body": "..."}
    objection_handling: str
    meeting_prep_questions: list[str]
    relevant_rayven_services: list[str]
    key_insights: str


class AICopilotService:
    """Provides private AI assistance to human operators managing active conversations."""

    def __init__(self, session: AsyncSession):
        self._db = session
        self._kb_agent = RayvenKnowledgeAgent(session)

    async def generate_copilot_dossier(
        self,
        conversation_id: uuid.UUID,
        llm: LLMProvider | None = None,
    ) -> CopilotRecommendations:
        """Generate private intelligence dossier & recommended responses for operator."""
        conv = await self._db.get(
            Conversation,
            conversation_id,
            options=[
                selectinload(Conversation.lead).selectinload(Lead.prospect).selectinload(Prospect.company),
                selectinload(Conversation.lead).selectinload(Lead.research),
                selectinload(Conversation.lead).selectinload(Lead.score),
                selectinload(Conversation.messages),
            ],
        )
        if not conv or not conv.lead:
            raise ValueError(f"Conversation {conversation_id} not found")

        lead = conv.lead
        prospect = lead.prospect
        company = prospect.company
        research = lead.research

        # Assemble thread history
        thread_lines = []
        for m in conv.messages:
            sender = prospect.full_name if m.direction == MessageDirection.INBOUND else "Rayven Outreach"
            thread_lines.append(f"[{m.direction.value.upper()}] {sender}: {m.body}")
        thread_text = "\n---\n".join(thread_lines) if thread_lines else "No messages recorded yet."

        # Fetch relevant Rayven KB context
        kb_results = []
        if llm:
            try:
                kb_results = await self._kb_agent.search_with_citations(
                    llm, query=f"{research.potential_challenge if research else ''} {thread_text[:200]}", k=3
                )
            except Exception:
                pass
        kb_text = "\n".join([r.content for r in kb_results]) if kb_results else "Rayven Framework: Context Intelligence, Narrative Architecture, Strategic Deployment, Outcome Measurement."

        if not llm:
            # Heuristic fallback dossier
            return CopilotRecommendations(
                conversation_summary=f"Conversation with {prospect.full_name} ({prospect.title or 'Executive'} @ {company.name if company else 'Prospect Firm'}).",
                recommended_replies=[
                    {
                        "tone": "Consultative",
                        "subject": f"Re: {conv.subject or 'Strategic Communications'}",
                        "body": f"Dear {prospect.first_name},\n\nThank you for reaching out. Based on your focus at {company.name if company else 'your firm'}, we would welcome a 15-minute discovery call to share how Rayven's narrative architecture framework aligns with your priorities.\n\nAre you available later this week?",
                    },
                ],
                objection_handling="Focus on outcome measurement and strategic narrative positioning.",
                meeting_prep_questions=[
                    f"What is your primary communication objective for Q3/Q4?",
                    f"How are your key stakeholders currently measuring brand trust?",
                ],
                relevant_rayven_services=["Narrative Architecture", "Context Intelligence Briefs"],
                key_insights=research.why_rayven_relevant if research else "High alignment with Rayven core services.",
            )

        system_prompt = (
            "You are an AI Deal Strategist & Copilot for Rayven Strategic Communications (RayvenSC).\n"
            "Your user is a human Rayven Director preparing to respond to an executive prospect.\n"
            "Analyze the conversation thread and research brief. Generate private copilot guidance JSON."
        )

        user_prompt = f"""
Prospect: {prospect.full_name} ({prospect.title or 'Executive'})
Company: {company.name if company else 'Organisation'} ({company.industry if company else 'Sector'})
Lead Score: {lead.score.total_score if lead.score else 'N/A'}/100

Company Research Context:
- Challenge: {research.potential_challenge if research else 'Market narrative positioning'}
- Rayven Relevance: {research.why_rayven_relevant if research else 'Strategic narrative architecture'}

Conversation Thread History:
{thread_text}

Rayven Framework KB Context:
{kb_text}

Generate JSON object:
- conversation_summary: 2-sentence summary of the conversation state and prospect's core interest
- recommended_replies: array of 3 distinct response draft objects:
  1. Consultative (Focus on understanding context before recommending communication)
  2. Direct (Focus on scheduling a 15-minute strategic discovery call)
  3. Executive Insight (Focus on sharing a relevant case study / framework insight)
  Each object has: tone, subject, body.
- objection_handling: guidance on addressing potential pushback or hesitations
- meeting_prep_questions: list of 3 strategic questions the human director should ask in a meeting
- relevant_rayven_services: list of 2-3 specific RayvenSC services most applicable (e.g. Narrative Architecture, Context Intelligence, Crisis Communication, Outcome Measurement)
- key_insights: 1 key commercial takeaway for the human director

Do NOT include markdown syntax around JSON.
"""

        try:
            raw = await llm.complete(
                [LLMMessage(role="system", content=system_prompt), LLMMessage(role="user", content=user_prompt)],
                temperature=0.4,
            )
            clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            data = json.loads(clean)

            dossier = CopilotRecommendations(
                conversation_summary=data.get("conversation_summary", "Active conversation thread."),
                recommended_replies=data.get("recommended_replies", []),
                objection_handling=data.get("objection_handling", "Focus on Rayven framework alignment."),
                meeting_prep_questions=data.get("meeting_prep_questions", []),
                relevant_rayven_services=data.get("relevant_rayven_services", ["Narrative Architecture"]),
                key_insights=data.get("key_insights", "High potential lead."),
            )

            # Store copilot data on conversation
            conv.copilot_data = data
            await self._db.commit()
            return dossier

        except Exception as e:
            logger.error(f"Copilot generation failed: {e}")
            return CopilotRecommendations(
                conversation_summary="Active thread.",
                recommended_replies=[],
                objection_handling="Error generating copilot data.",
                meeting_prep_questions=[],
                relevant_rayven_services=["Narrative Architecture"],
                key_insights=str(e),
            )
