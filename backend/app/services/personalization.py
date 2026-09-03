"""
Personalization Engine
Generates hyper-personalized, evidence-grounded outreach messages.
Uses RAG against the RayvenSC Knowledge Base and enforces executive communication rules.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.knowledge.ingestion import search_knowledge_base
from app.models import Campaign, EmailTemplate, Lead, Prospect, ProspectResearch
from app.providers.base import LLMMessage, LLMProvider

logger = logging.getLogger(__name__)


@dataclass
class GeneratedOutreach:
    subject: str
    body_text: str
    body_html: str
    reasoning: str


class PersonalizationService:
    """RAG-grounded outreach writer enforcing strategic communications tone."""

    def __init__(self, session: AsyncSession):
        self._db = session

    async def generate_outreach_email(
        self,
        lead_id: uuid.UUID,
        step_number: int = 1,
        llm: LLMProvider | None = None,
    ) -> GeneratedOutreach:
        """Generate a personalized initial email or follow-up for a lead."""
        from sqlalchemy.orm import selectinload
        stmt = (
            select(Lead)
            .where(Lead.id == lead_id)
            .options(
                selectinload(Lead.prospect).selectinload(Prospect.company),
                selectinload(Lead.campaign),
            )
        )
        res = await self._db.execute(stmt)
        lead = res.scalar_one_or_none()
        if not lead or not lead.prospect:
            raise ValueError(f"Lead {lead_id} missing prospect")

        prospect = lead.prospect
        company = prospect.company
        campaign = lead.campaign
        research = await self._get_prospect_research(lead.id)

        # 1. Auto-select strategic EmailTemplate framework based on prospect designation & signals
        selected_template = await self._auto_select_template(prospect, research, step_number)
        template_name = selected_template.name if selected_template else "Strategic Observation"
        template_purpose = selected_template.purpose if selected_template else "Start a conversation by identifying a meaningful observation."
        template_subject = selected_template.subject_template if selected_template else "A thought on {{company}}'s positioning"
        template_body_structure = selected_template.body_template if selected_template else "Hi {{first_name}}, ..."
        template_rules = selected_template.rules if selected_template else "Keep concise, peer-level consultative tone."

        # 2. Fetch relevant RAG chunks from RayvenSC Knowledge Base
        kb_query = f"{company.industry or ''} {campaign.value_proposition or ''} {research.potential_challenge if research else ''}"
        kb_chunks = []
        if llm:
            try:
                kb_chunks = await search_knowledge_base(self._db, llm, query=kb_query, k=3, threshold=0.60)
            except Exception as e:
                logger.warning(f"RAG search failed for personalization: {e}")

        kb_context_text = "\n---\n".join([f"[{c['title']}]: {c['content']}" for c in kb_chunks]) if kb_chunks else (
            "RayvenSC is a premier narrative architecture firm based in Abuja, Nigeria. "
            "Framework: Context Intelligence -> Narrative Architecture -> Strategic Deployment -> Outcome Measurement."
        )

        # 3. Build prompt enforcing selected strategic framework and brand rules
        system_prompt = (
            "You are a Senior Strategic Director at Rayven Strategic Communications (RayvenSC).\n"
            f"Your task is to write a high-converting, deeply strategic cold email using the selected framework: '{template_name}'.\n\n"
            f"STRATEGIC FRAMEWORK PURPOSE:\n{template_purpose}\n\n"
            f"FRAMEWORK SUBJECT PATTERN:\n{template_subject}\n\n"
            f"FRAMEWORK BODY STRUCTURE:\n{template_body_structure}\n\n"
            f"CRITICAL FRAMEWORK RULES:\n{template_rules}\n\n"
            "GENERAL WRITING RULES:\n"
            "1. NO fake familiarity or generic pleasantries (DO NOT write 'Hope this finds you well', 'I came across your profile', 'I hope you're having a great week').\n"
            "2. NO invented facts or unverified assumptions. Use ONLY the empirical evidence provided.\n"
            "3. Keep the email concise and authoritative (under 130 words).\n"
            "4. Communicate like a peer strategic consultant — authoritative, precise, respectful of executive time.\n"
            "5. CTA must be a low-friction invitation to explore.\n"
        )

        if step_number == 1:
            user_prompt = f"""
Prospect: {prospect.full_name}
Designation/Title: {prospect.title or 'Executive'}
Company: {company.name if company else 'their organisation'} ({company.industry if company else 'their sector'})
Location: {prospect.location or company.country if company else 'Africa'}

Empirical Business Research:
- Context: {research.company_context if research else 'Established market presence'}
- Verified Signals: {research.communication_signals if research else 'Navigating growth and stakeholder alignment'}
- Key Opportunity/Challenge: {research.potential_challenge if research else 'Differentiating narrative in a crowded market'}
- Why Rayven Relevant: {research.why_rayven_relevant if research else 'Building narrative architecture that turns positioning into trust'}

Selected Framework: {template_name}
Framework Target Designation: {selected_template.recommended_lead_types if selected_template else 'Executive'}

RayvenSC Knowledge Base Context:
{kb_context_text}

Rewrite and generate the outreach email following the '{template_name}' framework. Output JSON only with keys:
- subject: concise, compelling subject line following the framework pattern
- body_text: plain text email body (salutation, body paragraphs, sign-off as Rayven Strategic Communications)
- body_html: clean HTML paragraphs (<p> tags) matching body_text
- reasoning: 1-sentence rationale explaining why the '{template_name}' framework was auto-selected for this prospect's designation ({prospect.title or 'Executive'})
"""
        else: # Follow-up email
            user_prompt = f"""
Prospect: {prospect.full_name} ({prospect.title or 'Executive'})
Company: {company.name if company else 'their organisation'}
Follow-up Step: #{step_number}

Empirical Context:
- Previous outreach sent focused on: {campaign.value_proposition if campaign else 'Strategic narrative architecture'}
- Relevant Rayven Framework element: Outcome Measurement & Strategic Deployment

Write a brief (under 80 words) professional follow-up email adding a fresh strategic perspective or outcome metric without being pushy or passive-aggressive.

Generate JSON with keys: subject, body_text, body_html, reasoning.
"""

        if not llm:
            # Fallback template if LLM unavailable
            subj = f"Strategic Communications & Narrative Architecture for {company.name if company else 'Your Organisation'}"
            body = (
                f"Dear {prospect.first_name},\n\n"
                f"In operating within the {company.industry if company else 'market'} sector, the challenge is rarely generating content—it is ensuring that key stakeholders understand your direction with absolute clarity.\n\n"
                f"At Rayven Strategic Communications, we build narrative architecture for organisations navigating complex, multi-stakeholder environments. "
                f"Our framework aligns positioning with measurable outcome measurement.\n\n"
                f"Are you open to a brief conversation on how this framework can support your team's upcoming objectives?\n\n"
                f"Warm regards,\n"
                f"Rayven Strategic Communications\n"
                f"Abuja, Nigeria | hello@rayvensc.com"
            )
            return GeneratedOutreach(
                subject=subj,
                body_text=body,
                body_html=f"<p>{body.replace(chr(10), '<br>')}</p>",
                reasoning="Fallback static template used.",
            )

        try:
            raw = await llm.complete(
                [LLMMessage(role="system", content=system_prompt), LLMMessage(role="user", content=user_prompt)],
                temperature=0.4,
            )
            clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            data = json.loads(clean)
            return GeneratedOutreach(
                subject=data.get("subject", f"Strategic Communications — {company.name if company else ''}"),
                body_text=data.get("body_text", ""),
                body_html=data.get("body_html", f"<p>{data.get('body_text', '')}</p>"),
                reasoning=data.get("reasoning", "LLM generated personalization"),
            )
        except Exception as e:
            logger.error(f"Personalization generation failed: {e}")
            subj = f"Narrative Architecture & Positioning for {company.name if company else 'Your Brand'}"
            body = f"Dear {prospect.first_name},\n\nAt Rayven Strategic Communications, we help organisations close the gap between what they say and what the world actually understands.\n\nWould you be open to a brief exchange on aligning your narrative architecture with Q3 priorities?\n\nBest regards,\nRayven Strategic Communications"
            return GeneratedOutreach(
                subject=subj,
                body_text=body,
                body_html=f"<p>{body.replace(chr(10), '<br>')}</p>",
                reasoning="Fallback heuristic template due to error.",
            )

    async def _auto_select_template(
        self, prospect: Prospect, research: ProspectResearch | None, step_number: int
    ) -> EmailTemplate | None:
        """Automatically match the best strategic EmailTemplate framework based on prospect designation & research signals."""
        role = (prospect.title or "").lower()
        sig = (research.communication_signals or "").lower() if research else ""

        slug = "strategic_observation"
        if step_number == 2:
            slug = "followup_new_insight"
        elif step_number == 3:
            slug = "followup_strategic_idea"
        elif step_number == 4:
            slug = "followup_value_offer"
        elif step_number >= 5:
            slug = "breakup_close_loop"
        else:
            # Designation & Signal matching
            if any(w in role for w in ["founder", "ceo", "managing director", "speaker", "author"]):
                slug = "personal_brand"
            elif any(w in role for w in ["cmo", "marketing director", "head of brand", "vp marketing"]):
                slug = "brand_positioning" if "positioning" in sig else "digital_growth"
            elif any(w in role for w in ["sustainability", "csr", "impact", "esg"]):
                slug = "social_impact_csr"
            elif any(w in role for w in ["product", "cpo", "head of product"]):
                slug = "product_service_launch"
            elif any(w in role for w in ["growth", "expansion", "international", "territory"]):
                slug = "growth_expansion"
            elif any(w in role for w in ["strategy", "cso", "business development"]):
                slug = "market_intelligence"
            elif any(w in role for w in ["board", "chairman", "executive"]):
                slug = "executive_communication"

        stmt = select(EmailTemplate).where(EmailTemplate.slug == slug)
        res = await self._db.execute(stmt)
        matched = res.scalar_one_or_none()
        if not matched:
            res_fallback = await self._db.execute(select(EmailTemplate).where(EmailTemplate.is_active == True))
            matched = res_fallback.scalars().first()
        return matched

    async def _get_prospect_research(self, lead_id: uuid.UUID) -> ProspectResearch | None:
        stmt = select(ProspectResearch).where(ProspectResearch.lead_id == lead_id)
        res = await self._db.execute(stmt)
        return res.scalar_one_or_none()
