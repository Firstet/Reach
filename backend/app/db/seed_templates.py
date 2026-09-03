"""
Seed script for pre-populating the 15 Strategic RayvenSC Email Templates.
These templates serve as strategic frameworks for the Rayven AI Business Development Agent.
"""

from __future__ import annotations

import logging
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import EmailTemplate

logger = logging.getLogger(__name__)

RAYVEN_TEMPLATES = [
    {
        "slug": "strategic_observation",
        "name": "1. Strategic Observation",
        "category": "Initial Outreach",
        "purpose": "Start a conversation by identifying a meaningful communication or brand observation about the prospect's company.",
        "when_to_use": "When research identifies a specific public messaging, PR, or brand observation that can be analyzed constructively.",
        "when_not_to_use": "When research is generic or lacks a verified specific observation. Do not invent problems or sound like an audit.",
        "recommended_lead_types": "CEOs, CMOs, Managing Directors, Head of Brand",
        "subject_template": "A thought on {{company}}'s {{strategic_opportunity}}",
        "body_template": (
            "Hi {{first_name}},\n\n"
            "{{recent_signal}}\n\n"
            "{{strategic_opportunity}}\n\n"
            "At Rayven, we work with organizations on the space between what they say and how they are understood. "
            "I thought there may be an interesting opportunity worth exploring around your narrative positioning.\n\n"
            "Open to a brief exchange on this angle when convenient?"
        ),
        "rules": "- Never use generic compliments.\n- Observation must be specific.\n- Do not invent problems.\n- Do not sound like an audit unless requested.\n- Keep concise under 120 words.",
        "tone": "Consultative & Authoritative",
        "max_length": "120 words",
        "cta_style": "Low-pressure conversational",
        "follow_up_rules": "Follow up after 72 hours with a fresh insight.",
        "variables": ["first_name", "company", "recent_signal", "strategic_opportunity"],
        "rayven_capabilities": ["Strategic Communications", "Narrative Architecture", "Brand Strategy"],
    },
    {
        "slug": "growth_expansion",
        "name": "2. Growth / Expansion",
        "category": "Initial Outreach",
        "purpose": "Target companies experiencing growth, expansion, new market entry or significant business development.",
        "when_to_use": "Research identifies geographic expansion, new market entry, major growth, new business units, acquisitions, or rapid scaling.",
        "when_not_to_use": "Stagnant companies or companies currently downsizing.",
        "recommended_lead_types": "Founders, Chief Growth Officers, VP Expansion, Managing Directors",
        "subject_template": "Navigating growth: Strategic messaging for {{company}}",
        "body_template": (
            "Hi {{first_name}},\n\n"
            "I noticed {{company}}'s recent expansion and momentum in {{recent_signal}}.\n\n"
            "Rapid scaling frequently creates a positioning challenge where new market perception lags behind operational capacity.\n\n"
            "Rayven helps growth-stage enterprises engineer narrative architecture and market positioning to ensure reputation scales alongside business expansion.\n\n"
            "Would you be open to an initial discussion on how your positioning is evolving with this growth?"
        ),
        "rules": "- Identify the growth signal.\n- Explain why growth creates positioning challenge.\n- Connect to Rayven capabilities.\n- Invite discussion rather than forcing a meeting.",
        "tone": "Strategic & Growth-oriented",
        "max_length": "140 words",
        "cta_style": "Invite strategic discussion",
        "follow_up_rules": "Follow up with market expansion benchmark data.",
        "variables": ["first_name", "company", "recent_signal"],
        "rayven_capabilities": ["Strategic Communications", "Brand Strategy", "Market Intelligence & Growth Research", "Narrative Architecture"],
    },
    {
        "slug": "brand_positioning",
        "name": "3. Brand Positioning",
        "category": "Initial Outreach",
        "purpose": "Approach companies where the product/business appears stronger than the way the brand is positioned.",
        "when_to_use": "When differentiation, positioning, messaging, brand architecture, narrative consistency, or perception can be elevated.",
        "when_not_to_use": "Never tell a prospect their branding is 'bad'. Frame as an opportunity.",
        "recommended_lead_types": "CEOs, Chief Marketing Officers, Brand Directors, Founders",
        "subject_template": "Elevating {{company}}'s market positioning",
        "body_template": (
            "Hi {{first_name}},\n\n"
            "What {{company}} has built in {{recent_signal}} is impressive.\n\n"
            "However, there appears to be an opportunity for your public positioning to even more strongly reflect your actual market strength and capability.\n\n"
            "Rayven specializes in positioning strategy and narrative consistency to ensure high-value enterprises command the trust and authority they deserve.\n\n"
            "Are you open to a brief conversational exchange on this positioning angle?"
        ),
        "rules": "- Observation → positioning implication → opportunity → Rayven relevance → conversational CTA.\n- Focus on differentiation, positioning, messaging, perception.\n- Never criticize branding.",
        "tone": "Consultative & Elevating",
        "max_length": "130 words",
        "cta_style": "Low-pressure conversational",
        "follow_up_rules": "Follow up with positioning framework example.",
        "variables": ["first_name", "company", "recent_signal"],
        "rayven_capabilities": ["Brand Strategy", "Narrative Architecture", "Strategic Communications"],
    },
    {
        "slug": "communication_gap",
        "name": "4. Communication Gap",
        "category": "Initial Outreach",
        "purpose": "Identify situations where there appears to be a gap between what a company does and how clearly it communicates it.",
        "when_to_use": "Evidence from website, LinkedIn, campaigns, or announcements shows gap between capability and public narrative.",
        "when_not_to_use": "Do not make unsupported criticism or unverified claims.",
        "recommended_lead_types": "CEOs, Head of Corporate Communications, Chief Commercial Officers",
        "subject_template": "Bridging the narrative gap at {{company}}",
        "body_template": (
            "Hi {{first_name}},\n\n"
            "Looking at {{company}}'s work in {{recent_signal}}, what your team is building is exceptionally strong.\n\n"
            "Yet what the organization is doing may be stronger than what its public communication currently communicates.\n\n"
            "At Rayven, we help leadership teams bridge the gap between organizational capability and public perception through precision narrative strategy.\n\n"
            "Would you be open to exploring how this gap could be closed?"
        ),
        "rules": "- Core idea: 'What the organization is doing may be stronger than what its communication currently communicates.'\n- Use evidence from public channels.\n- Connect naturally to Rayven.",
        "tone": "Empathetic & Insightful",
        "max_length": "130 words",
        "cta_style": "Soft discussion invitation",
        "follow_up_rules": "Follow up with narrative alignment case note.",
        "variables": ["first_name", "company", "recent_signal"],
        "rayven_capabilities": ["Strategic Communications", "Narrative Architecture", "PR"],
    },
    {
        "slug": "digital_growth",
        "name": "5. Digital Growth",
        "category": "Initial Outreach",
        "purpose": "Approach companies with visible marketing activity but an opportunity to improve strategic consistency, digital growth or communication effectiveness.",
        "when_to_use": "Inconsistent messaging, fragmented channels, campaigns without narrative consistency, or content volume without positioning.",
        "when_not_to_use": "Companies with zero digital presence or dormant channels.",
        "recommended_lead_types": "CMOs, Head of Marketing, Digital Growth Leads, Commercial Directors",
        "subject_template": "Strategic digital cohesion for {{company}}",
        "body_template": (
            "Hi {{first_name}},\n\n"
            "I have been following {{company}}'s active digital campaigns around {{recent_signal}}.\n\n"
            "While your volume of activity is strong, there appears to be an opportunity to align your messaging across channels into a unified, high-converting growth narrative.\n\n"
            "Rayven's Digital Growth & Strategic Communications practice aligns brand positioning with digital channels to maximize narrative impact.\n\n"
            "Open to a brief strategic exchange on channel cohesion?"
        ),
        "rules": "- Look for inconsistent messaging, fragmented channels, weak strategic cohesion.\n- Only select the most relevant capability.",
        "tone": "Direct & Practical",
        "max_length": "140 words",
        "cta_style": "Conversational exchange",
        "follow_up_rules": "Follow up with digital narrative alignment insight.",
        "variables": ["first_name", "company", "recent_signal"],
        "rayven_capabilities": ["Digital Growth & Marketing", "Strategic Communications", "Brand Strategy", "Narrative Architecture"],
    },
    {
        "slug": "personal_brand",
        "name": "6. Personal Brand",
        "category": "Initial Outreach",
        "purpose": "Approach founders and senior executives whose expertise, visibility or public positioning creates a personal-brand opportunity.",
        "when_to_use": "Executive is publicly visible, speaks publicly, publishes thought leadership, leads growing company, or has strong reputation.",
        "when_not_to_use": "Avoid shallow compliments. Do not use for quiet leaders who actively avoid public presence.",
        "recommended_lead_types": "Founders, CEOs, Managing Directors, Keynote Speakers",
        "subject_template": "Thought leadership & narrative architecture for {{first_name}}",
        "body_template": (
            "Hi {{first_name}},\n\n"
            "Your recent commentary on {{recent_signal}} highlights your deep expertise in {{industry}}.\n\n"
            "For leaders driving category growth, executive visibility is not about self-promotion—it is about turning personal authority into institutional trust and enterprise leverage.\n\n"
            "Rayven's Executive Personal Brand Architecture helps founders convert public visibility into strategic market influence.\n\n"
            "Would you be open to a peer-level exchange on structuring your narrative platform?"
        ),
        "rules": "- Do not use shallow compliments.\n- Focus on the relationship between expertise, perception, positioning, and influence.",
        "tone": "Authoritative & Executive",
        "max_length": "130 words",
        "cta_style": "Peer-level conversation",
        "follow_up_rules": "Follow up with executive positioning framework.",
        "variables": ["first_name", "industry", "recent_signal"],
        "rayven_capabilities": ["Personal Brand Architecture", "Executive Communications", "Strategic Communications"],
    },
    {
        "slug": "market_entry",
        "name": "7. Market Entry",
        "category": "Initial Outreach",
        "purpose": "Approach organizations entering a new geographic, cultural or commercial market.",
        "when_to_use": "Expansion into new territory, entering new vertical, or cultural market expansion.",
        "when_not_to_use": "Do not assume a company needs help simply because it is expanding without a credible communication reason.",
        "recommended_lead_types": "Head of Market Entry, Managing Director Africa/Regional, VP Global Expansion",
        "subject_template": "Local narrative & market entry strategy for {{company}}",
        "body_template": (
            "Hi {{first_name}},\n\n"
            "Congratulations on {{company}}'s move into {{recent_signal}}.\n\n"
            "Entering new commercial or geographic markets introduces cultural and stakeholder complexity where standard corporate messaging often fails to build local trust.\n\n"
            "Rayven provides Context Intelligence & Strategic PR to position expanding brands authentically within regional ecosystems.\n\n"
            "Open to a low-pressure discussion on your local market entry narrative?"
        ),
        "rules": "- Market signal → communication complexity → context/narrative opportunity → Rayven relevance → conversation.\n- Avoid assuming company needs help without credible reason.",
        "tone": "Context-aware & Strategic",
        "max_length": "140 words",
        "cta_style": "Low-pressure discussion",
        "follow_up_rules": "Follow up with regional context intelligence note.",
        "variables": ["first_name", "company", "recent_signal"],
        "rayven_capabilities": ["Context Intelligence", "Market Intelligence & Growth Research", "Brand Strategy", "Strategic Communications"],
    },
    {
        "slug": "product_service_launch",
        "name": "8. Product / Service Launch",
        "category": "Initial Outreach",
        "purpose": "Approach organizations launching a new product, service or initiative.",
        "when_to_use": "New product launch, service rollout, or strategic initiative announcement.",
        "when_not_to_use": "Do not simply congratulate the company and pitch services.",
        "recommended_lead_types": "Chief Product Officer, CMO, Head of Product Marketing, VP Innovation",
        "subject_template": "Narrative differentiation for {{recent_signal}}",
        "body_template": (
            "Hi {{first_name}},\n\n"
            "I saw the announcement regarding {{company}}'s launch of {{recent_signal}}.\n\n"
            "The key challenge with major launches is ensuring the market grasps the category-defining value beyond basic feature announcements.\n\n"
            "Rayven's Campaign Development & Brand Strategy practice builds launch narratives that establish category leadership.\n\n"
            "Would you be open to a brief exchange on how this launch narrative is being received?"
        ),
        "rules": "- Analyze what is launched, target audience, messaging clarity, narrative differentiation.\n- Do not just congratulate.",
        "tone": "Dynamic & High-Impact",
        "max_length": "130 words",
        "cta_style": "Strategic launch exchange",
        "follow_up_rules": "Follow up with launch messaging differentiation insight.",
        "variables": ["first_name", "company", "recent_signal"],
        "rayven_capabilities": ["Brand Strategy", "Campaign Development", "Strategic Communications", "Digital Growth"],
    },
    {
        "slug": "executive_communication",
        "name": "9. Executive Communication",
        "category": "Initial Outreach",
        "purpose": "Target senior executives or organizations where leadership communication may be strategically important.",
        "when_to_use": "CEO visibility, corporate transformation, major announcements, stakeholder communication, reputation management, or org change.",
        "when_not_to_use": "Low-level staff outreach.",
        "recommended_lead_types": "CEOs, Board Chairs, Chief Communications Officers, VP Corporate Affairs",
        "subject_template": "Stakeholder narrative & leadership positioning",
        "body_template": (
            "Hi {{first_name}},\n\n"
            "As {{company}} navigates {{recent_signal}}, executive communication becomes the primary lever for maintaining stakeholder alignment and market confidence.\n\n"
            "During major organizational milestones, clear leadership positioning separates industry benchmarks from reactive brands.\n\n"
            "Rayven's Executive Communications practice works with C-Suite leaders to craft authoritative narrative frameworks.\n\n"
            "Open to an executive exchange on aligning leadership narrative with corporate objectives?"
        ),
        "rules": "- Target senior leadership.\n- Relevant capabilities: Executive Communications, Strategic Communications, PR, Reputation Management.",
        "tone": "C-Suite Peer & High-level",
        "max_length": "125 words",
        "cta_style": "Executive exchange",
        "follow_up_rules": "Follow up with C-Suite stakeholder alignment checklist.",
        "variables": ["first_name", "company", "recent_signal"],
        "rayven_capabilities": ["Executive Communications", "Strategic Communications", "PR", "Personal Brand Architecture", "Reputation Management"],
    },
    {
        "slug": "social_impact_csr",
        "name": "10. Social Impact / CSR",
        "category": "Initial Outreach",
        "purpose": "Approach organizations doing meaningful social impact, CSR or sustainability work.",
        "when_to_use": "Company active in CSR, ESG, sustainability, or community impact work.",
        "when_not_to_use": "Do not imply company's impact is weak. Frame as making meaningful work clearer.",
        "recommended_lead_types": "Head of Sustainability, Chief Impact Officer, Corporate Affairs Director, CEO",
        "subject_template": "Amplifying {{company}}'s social impact narrative",
        "body_template": (
            "Hi {{first_name}},\n\n"
            "I was reading about {{company}}'s initiative in {{recent_signal}}.\n\n"
            "Authentic sustainability and social impact work often struggles to receive the public clarity and institutional credibility it deserves.\n\n"
            "Rayven's CSR & Social Impact practice helps leaders articulate purpose-driven work into compelling, stakeholder-trusted narratives.\n\n"
            "Would you be open to a brief exchange on how your impact storytelling is structured?"
        ),
        "rules": "- Do not imply impact is weak.\n- Frame communication as making meaningful work clearer, more credible, and strategically understood.",
        "tone": "Purpose-driven & Credible",
        "max_length": "130 words",
        "cta_style": "Impact narrative exchange",
        "follow_up_rules": "Follow up with ESG impact storytelling case note.",
        "variables": ["first_name", "company", "recent_signal"],
        "rayven_capabilities": ["CSR & Social Impact", "Strategic Communications", "PR"],
    },
    {
        "slug": "market_intelligence",
        "name": "11. Market Intelligence",
        "category": "Initial Outreach",
        "purpose": "Approach organizations where market knowledge, audience understanding, competitive intelligence or market-entry intelligence could support growth.",
        "when_to_use": "Entering new markets, changing consumer behavior, competitive pressure, new product categories, industry shifts, or repositioning.",
        "when_not_to_use": "Static businesses with no market shifts.",
        "recommended_lead_types": "Chief Strategy Officer, VP Market Intelligence, Head of Business Development",
        "subject_template": "Market intelligence & growth insights for {{company}}",
        "body_template": (
            "Hi {{first_name}},\n\n"
            "With the recent market shifts in {{recent_signal}}, staying ahead of audience sentiment and competitive positioning is critical for growth.\n\n"
            "Rayven's Market Intelligence & Growth Research team equips enterprise leaders with actionable contextual research and competitor narrative tracking.\n\n"
            "Would you be open to reviewing a short sample of our market intelligence insights for your category?"
        ),
        "rules": "- Use evidence such as market entry, changing consumer behavior, competitive pressure.\n- Focus on actionable insights.",
        "tone": "Data-driven & Insightful",
        "max_length": "135 words",
        "cta_style": "Insight-sharing invitation",
        "follow_up_rules": "Follow up with category intelligence snippet.",
        "variables": ["first_name", "company", "recent_signal"],
        "rayven_capabilities": ["Market Intelligence & Growth Research", "Brand Strategy", "Context Intelligence"],
    },
    {
        "slug": "followup_new_insight",
        "name": "12. Follow-Up: New Insight",
        "category": "Follow-up",
        "purpose": "Follow up when the prospect has not responded without using generic check-in phrases.",
        "when_to_use": "Step 2 outreach after initial message goes unanswered.",
        "when_not_to_use": "NEVER write 'Just following up', 'Just checking in', or 'Following up on my previous email'.",
        "recommended_lead_types": "All prospects at Step 2",
        "subject_template": "Additional thought on {{company}}'s {{strategic_opportunity}}",
        "body_template": (
            "Hi {{first_name}},\n\n"
            "Following up on my note regarding {{company}}'s positioning—I noticed another interesting development in {{recent_signal}}.\n\n"
            "This further highlights how narrative consistency can directly influence stakeholder trust during key growth phases.\n\n"
            "Thought this perspective might be valuable as you review your upcoming priorities.\n\n"
            "Open to a quick exchange if this resonates?"
        ),
        "rules": "- Reference original idea briefly.\n- Introduce new relevant insight.\n- Explain why it matters.\n- Soft CTA.",
        "tone": "Valuable & Unintrusive",
        "max_length": "110 words",
        "cta_style": "Soft conversational",
        "follow_up_rules": "Proceed to Step 3 Strategic Idea after 72h.",
        "variables": ["first_name", "company", "recent_signal", "strategic_opportunity"],
        "rayven_capabilities": ["Strategic Communications", "Narrative Architecture"],
    },
    {
        "slug": "followup_strategic_idea",
        "name": "13. Follow-Up: Strategic Idea",
        "category": "Follow-up",
        "purpose": "Provide a useful strategic thought after no response.",
        "when_to_use": "Step 3 outreach after no response.",
        "when_not_to_use": "Generic sales pitches. Must create 'That's an interesting point' rather than 'They are selling me'.",
        "recommended_lead_types": "All prospects at Step 3",
        "subject_template": "A strategic idea for {{company}}",
        "body_template": (
            "Hi {{first_name}},\n\n"
            "I had a quick strategic thought regarding how {{company}} could approach your positioning around {{recent_signal}}:\n\n"
            "Rather than treating messaging as publicity, framing your narrative around institutional credibility typically increases high-value prospect engagement by aligning trust before sales conversations.\n\n"
            "We frequently implement this model for category leaders.\n\n"
            "Let me know if you would like me to share a 1-page summary of this model."
        ),
        "rules": "- Generate short, relevant idea.\n- Demonstrate Rayven's thinking without giving away entire consulting engagement.\n- Create 'That's an interesting point' reaction.",
        "tone": "Consultative & Thought-provoking",
        "max_length": "110 words",
        "cta_style": "Low-pressure exchange",
        "follow_up_rules": "Proceed to Step 4 Value Offer after 72h.",
        "variables": ["first_name", "company", "recent_signal"],
        "rayven_capabilities": ["Brand Strategy", "Narrative Architecture"],
    },
    {
        "slug": "followup_value_offer",
        "name": "14. Follow-Up: Value Offer",
        "category": "Follow-up",
        "purpose": "Offer something useful such as a short strategic observation, mini communication thought, or market insight.",
        "when_to_use": "Step 4 outreach before final break-up.",
        "when_not_to_use": "Never fabricate a case study or result. Never promise free audit unless campaign enables it.",
        "recommended_lead_types": "All prospects at Step 4",
        "subject_template": "Strategic narrative observation for {{company}}",
        "body_template": (
            "Hi {{first_name}},\n\n"
            "Our team recently synthesized a brief 3-point narrative benchmark for companies navigating growth in {{industry}}.\n\n"
            "It highlights key positioning opportunities and common communication friction points.\n\n"
            "Should I send the 3-point summary over for your team to review?"
        ),
        "rules": "- Offer something useful.\n- Never fabricate case studies.\n- Never promise free audit unless campaign enables it.",
        "tone": "Generous & Professional",
        "max_length": "100 words",
        "cta_style": "Permission-based value offer",
        "follow_up_rules": "Proceed to Break-up after 96h.",
        "variables": ["first_name", "company", "industry"],
        "rayven_capabilities": ["Strategic Communications", "Market Intelligence & Growth Research"],
    },
    {
        "slug": "breakup_close_loop",
        "name": "15. Break-Up / Close The Loop",
        "category": "Break-up",
        "purpose": "End the automated sequence respectfully with confidence and professionalism.",
        "when_to_use": "Final step in automated outreach sequence.",
        "when_not_to_use": "Mid-sequence outreach.",
        "recommended_lead_types": "Unresponsive prospects at final step",
        "subject_template": "Closing the loop / {{company}}",
        "body_template": (
            "Hi {{first_name}},\n\n"
            "I assume strategic communications and brand narrative architecture aren't top priorities for {{company}} right now, so I will step back and stop my outreach.\n\n"
            "If priorities shift down the road and you want to explore how Rayven can support your positioning, feel free to reconnect anytime.\n\n"
            "Wishing you and {{company}} continued success.\n\n"
            "Best regards,\n"
            "Rayven Strategic Communications Team"
        ),
        "rules": "- Confident, brief, professional, no guilt, no pressure.\n- Communicate Rayven will step back.\n- STOP AUTOMATED OUTREACH AFTER THIS.",
        "tone": "Polite, Confident & Definitive",
        "max_length": "80 words",
        "cta_style": "No pressure close",
        "follow_up_rules": "Stop automated outreach permanently. Move lead to nurture / archived.",
        "variables": ["first_name", "company"],
        "rayven_capabilities": ["Strategic Communications"],
    },
]


async def seed_email_templates(db: AsyncSession) -> None:
    """Ensure all 15 RayvenSC strategic templates are populated in the database."""
    try:
        stmt = select(EmailTemplate)
        res = await db.execute(stmt)
        existing = {t.slug: t for t in res.scalars().all() if t.slug}

        added_count = 0
        updated_count = 0

        for item in RAYVEN_TEMPLATES:
            slug = item["slug"]
            if slug in existing:
                # Update existing template to ensure latest Rayven rules
                t = existing[slug]
                t.name = item["name"]
                t.category = item["category"]
                t.purpose = item["purpose"]
                t.when_to_use = item["when_to_use"]
                t.when_not_to_use = item["when_not_to_use"]
                t.recommended_lead_types = item["recommended_lead_types"]
                t.subject_template = item["subject_template"]
                t.body_template = item["body_template"]
                t.rules = item["rules"]
                t.tone = item["tone"]
                t.max_length = item["max_length"]
                t.cta_style = item["cta_style"]
                t.follow_up_rules = item["follow_up_rules"]
                t.variables = item["variables"]
                t.rayven_capabilities = item["rayven_capabilities"]
                updated_count += 1
            else:
                new_tmpl = EmailTemplate(
                    id=uuid.uuid4(),
                    slug=slug,
                    name=item["name"],
                    category=item["category"],
                    purpose=item["purpose"],
                    when_to_use=item["when_to_use"],
                    when_not_to_use=item["when_not_to_use"],
                    recommended_lead_types=item["recommended_lead_types"],
                    subject_template=item["subject_template"],
                    body_template=item["body_template"],
                    rules=item["rules"],
                    tone=item["tone"],
                    max_length=item["max_length"],
                    cta_style=item["cta_style"],
                    follow_up_rules=item["follow_up_rules"],
                    is_active=True,
                    variables=item["variables"],
                    rayven_capabilities=item["rayven_capabilities"],
                )
                db.add(new_tmpl)
                added_count += 1

        await db.commit()
        logger.info(f"RayvenSC Templates Seeding Complete: {added_count} added, {updated_count} updated.")
    except Exception as e:
        logger.error(f"Error seeding email templates: {e}")
        await db.rollback()
