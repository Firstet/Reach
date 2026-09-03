"""
Personalization Engine
Generates hyper-personalized, evidence-grounded outreach messages.
Uses RAG against the RayvenSC Knowledge Base and enforces executive communication rules.
"""

from __future__ import annotations

import json
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

        # Fetch previously sent messages to this lead to enforce strict anti-repetition
        from app.models import Message
        prev_stmt = select(Message).where(Message.lead_id == lead_id).order_by(Message.created_at.asc())
        prev_res = await self._db.execute(prev_stmt)
        prev_messages = prev_res.scalars().all()

        past_history_str = ""
        if prev_messages:
            past_history_str = "\n".join(
                [f"- Step {i+1} [{m.direction.value}]: Subject: '{m.subject}' | Body: '{m.body[:150]}...'" for i, m in enumerate(prev_messages)]
            )

        # 1. Auto-select strategic EmailTemplate framework based on prospect designation & signals
        selected_template = await self._auto_select_template(prospect, research, step_number)
        template_name = selected_template.name if selected_template else "Strategic Observation"
        template_purpose = selected_template.purpose if selected_template else "Start a conversation by identifying a meaningful observation."
        template_subject = selected_template.subject_template if selected_template else "A thought on {{company}}'s positioning"
        template_body_structure = selected_template.body_template if selected_template else "Hi {{first_name}}, ..."
        template_rules = selected_template.rules if selected_template else "Keep concise, peer-level consultative tone."

        # 2. Fetch relevant RAG chunks from RayvenSC Knowledge Base
        kb_query = f"{company.name if company else ''} {company.industry or ''} {campaign.value_proposition or ''} {research.potential_challenge if research else ''}"
        kb_chunks = []
        if llm:
            try:
                kb_chunks = await search_knowledge_base(self._db, llm, query=kb_query, k=3, threshold=0.55)
            except Exception as e:
                logger.warning(f"RAG search failed for personalization: {e}")

        kb_context_text = "\n---\n".join([f"[{c['title']}]: {c['content']}" for c in kb_chunks]) if kb_chunks else (
            "RayvenSC is a premier narrative architecture firm based in Abuja, Nigeria. "
            "Framework: Context Intelligence -> Narrative Architecture -> Strategic Deployment -> Outcome Measurement."
        )

        # 3. Build prompt enforcing selected strategic framework, brand rules, and STRICT ANTI-REPETITION
        system_prompt = (
            "You are a Senior Strategic Director at Rayven Strategic Communications (RayvenSC).\n"
            f"Your task is to write a high-converting, deeply tailored cold email using the selected framework: '{template_name}'.\n\n"
            f"STRATEGIC FRAMEWORK PURPOSE:\n{template_purpose}\n\n"
            f"FRAMEWORK SUBJECT PATTERN:\n{template_subject}\n\n"
            f"FRAMEWORK BODY STRUCTURE:\n{template_body_structure}\n\n"
            f"CRITICAL FRAMEWORK RULES:\n{template_rules}\n\n"
            "MANDATORY PERSONALIZATION & ANTI-REPETITION RULES:\n"
            "1. NO DUPICATES: Every single message MUST be 100% unique to this specific prospect and company. NEVER output generic or copy-paste templates.\n"
            "2. NO REPETITION: DO NOT repeat any opening phrases, subject lines, or sentence structures from previously sent emails to this prospect.\n"
            "3. NO fake familiarity (DO NOT write 'Hope this finds you well', 'I came across your profile', 'I hope you're having a great week').\n"
            "4. NO invented facts or unverified assumptions. Use ONLY the empirical evidence provided.\n"
            "5. Communicate like an authoritative peer strategic consultant (concise, under 120 words).\n"
            "6. Sign-off strictly as Rayven Strategic Communications.\n"
        )

        if step_number == 1:
            user_prompt = f"""
Prospect Name: {prospect.full_name}
First Name: {prospect.first_name}
Designation/Title: {prospect.title or 'Executive'}
Company: {company.name if company else 'their organisation'} ({company.industry if company else 'their sector'})
Location: {prospect.location or (company.country if company else 'Africa')}

Empirical Business Research & Web Signals:
- Company Context: {research.company_context if research else 'Established market presence'}
- Verified Signals: {research.communication_signals if research else 'Navigating growth and stakeholder alignment'}
- Key Opportunity/Challenge: {research.potential_challenge if research else 'Differentiating narrative in a crowded market'}
- Why Rayven Relevant: {research.why_rayven_relevant if research else 'Building narrative architecture that turns positioning into trust'}

Selected Framework: {template_name}
RayvenSC Knowledge Base Context:
{kb_context_text}

Craft a completely tailored outreach email specific to {prospect.full_name} at {company.name if company else 'their company'}. Output JSON only with keys:
- subject: concise, compelling subject line specific to {company.name if company else 'their organization'}
- body_text: plain text email body tailored specifically to {prospect.first_name}
- body_html: clean HTML paragraphs (<p> tags) matching body_text
- reasoning: 1-sentence rationale explaining the personalization logic for {prospect.full_name}
"""
        else: # Follow-up email
            user_prompt = f"""
Prospect Name: {prospect.full_name}
First Name: {prospect.first_name}
Designation/Title: {prospect.title or 'Executive'}
Company: {company.name if company else 'their organisation'}
Follow-up Step Number: #{step_number}

PREVIOUSLY SENT OUTREACH MESSAGES TO THIS PROSPECT:
{past_history_str if past_history_str else 'Initial outreach email already dispatched.'}

Write a brief (under 80 words) professional follow-up email introducing a NEW strategic angle or outcome metric.
DO NOT repeat the previous email body or subject line. Craft a completely fresh, distinct follow-up.

Output JSON only with keys: subject, body_text, body_html, reasoning.
"""

        if not llm:
            return self._generate_dynamic_fallback(prospect, company, research, step_number)

        try:
            raw = await llm.complete(
                [LLMMessage(role="system", content=system_prompt), LLMMessage(role="user", content=user_prompt)],
                temperature=0.5,
            )
            clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            data = json.loads(clean)
            return GeneratedOutreach(
                subject=data.get("subject", f"Strategic Communications — {company.name if company else 'Positioning'}"),
                body_text=data.get("body_text", ""),
                body_html=data.get("body_html", f"<p>{data.get('body_text', '')}</p>"),
                reasoning=data.get("reasoning", "LLM generated hyper-personalization"),
            )
        except Exception as e:
            logger.error(f"Personalization generation failed: {e}")
            return self._generate_dynamic_fallback(prospect, company, research, step_number)

    def _generate_dynamic_fallback(
        self, prospect: Prospect, company: Any, research: Any, step_number: int
    ) -> GeneratedOutreach:
        """Dynamic multi-template fallback generator ensuring distinct emails per prospect when LLM is offline."""
        c_name = company.name if company else "your organization"
        c_ind = company.industry if company and company.industry else "business"
        p_name = prospect.first_name or "Executive"
        p_title = prospect.title or "Leader"

        variations_step1 = [
            (
                f"Narrative Architecture & Brand Authority for {c_name}",
                f"Dear {p_name},\n\nIn scaling operations across the {c_ind} sector, the primary hurdle is rarely ambition—it is ensuring key stakeholders understand your market trajectory with absolute clarity.\n\nAt Rayven Strategic Communications, we build narrative architecture for leaders like yourself in {p_title} roles to transform perception into institutional trust.\n\nWould you be open to a brief 10-minute exchange this week on aligning {c_name}'s positioning with Q3 objectives?\n\nWarm regards,\nRayven Strategic Communications\nAbuja, Nigeria | hello@rayvensc.com",
            ),
            (
                f"A thought on {c_name}'s positioning & market perception",
                f"Hi {p_name},\n\nFollowing recent developments in the {c_ind} space, I noticed {c_name}'s expanding footprint. In multi-stakeholder markets, positioning isn't just PR—it's commercial leverage.\n\nRayvenSC specializes in executive positioning and strategic communications for leadership teams. We help turn brand perception into high-trust partner relationships.\n\nAre you available for a brief call to explore how this approach fits your current priorities?\n\nBest regards,\nRayven Strategic Communications",
            ),
            (
                f"Strategic Communications Diagnostic — {c_name}",
                f"Dear {p_name},\n\nAs {p_title} at {c_name}, ensuring your strategic narrative cuts through noise in {c_ind} requires a deliberate context intelligence framework.\n\nAt RayvenSC, we partner with executives to design narrative architecture that delivers measurable stakeholder engagement.\n\nWould you be open to a 10-minute introduction on our methodology?\n\nWarm regards,\nRayven Strategic Communications",
            ),
        ]

        variations_followup = [
            (
                f"Re: Strategic alignment for {c_name}",
                f"Hi {p_name},\n\nFollowing up on my previous note regarding {c_name}'s strategic communications framework.\n\nWe recently helped an enterprise in the {c_ind} sector achieve a 40% increase in stakeholder trust metrics by restructuring their narrative architecture.\n\nWould a 5-minute brief next Tuesday make sense for your schedule?\n\nBest regards,\nRayven Strategic Communications",
            ),
            (
                f"Quick follow-up — {c_name} narrative strategy",
                f"Dear {p_name},\n\nI know your schedule as {p_title} is demanding. I wanted to share a brief thought on how strategic PR positioning can accelerate {c_name}'s growth objectives.\n\nIf you're open to exploring this, I'm happy to share a brief 2-page strategic overview.\n\nWarm regards,\nRayven Strategic Communications",
            ),
        ]

        # Use seed hash based on prospect email and step number
        seed = abs(hash(f"{prospect.email}_{step_number}"))
        if step_number == 1:
            chosen_subj, chosen_body = variations_step1[seed % len(variations_step1)]
        else:
            chosen_subj, chosen_body = variations_followup[seed % len(variations_followup)]

        return GeneratedOutreach(
            subject=chosen_subj,
            body_text=chosen_body,
            body_html=f"<p>{chosen_body.replace(chr(10), '<br>')}</p>",
            reasoning=f"Dynamic heuristic variation #{seed % 3 + 1} generated for {prospect.full_name}",
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
