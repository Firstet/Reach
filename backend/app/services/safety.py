"""
Safety & Compliance Service
Enforces global kill switch, domain/email suppression, duplicate detection,
unsubscribe handling, and send limits.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Campaign, CampaignStatus, Lead, LeadStatus, Prospect, Suppression

logger = logging.getLogger(__name__)

# In-memory kill switch flag (can also be toggled via DB / config)
_GLOBAL_KILL_SWITCH = False


def set_global_kill_switch(active: bool) -> None:
    global _GLOBAL_KILL_SWITCH
    _GLOBAL_KILL_SWITCH = active
    logger.warning(f"Global kill switch set to: {active}")


def is_global_kill_switch_active() -> bool:
    return _GLOBAL_KILL_SWITCH


class SafetyService:
    """Provides compliance, safety, and rate-limiting validation."""

    def __init__(self, session: AsyncSession):
        self._db = session

    async def is_suppressed(self, email: str | None, domain: str | None = None) -> bool:
        """Check if an email address or company domain is suppressed."""
        if not email and not domain:
            return False

        conditions = []
        if email:
            conditions.append(
                (Suppression.suppression_type == "email") & (Suppression.value == email.lower().strip())
            )
        if domain:
            conditions.append(
                (Suppression.suppression_type == "domain") & (Suppression.value == domain.lower().strip())
            )

        from sqlalchemy import or_
        stmt = select(Suppression).where(or_(*conditions))
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def is_duplicate_lead(self, prospect_id: uuid.UUID, campaign_id: uuid.UUID) -> bool:
        """Check if prospect is already enrolled in this campaign."""
        stmt = select(Lead).where(
            Lead.prospect_id == prospect_id,
            Lead.campaign_id == campaign_id,
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def can_send_to_lead(self, lead: Lead) -> tuple[bool, str]:
        """
        Comprehensive check before sending outreach to a lead.
        Returns (can_send: bool, reason: str).
        """
        # 1. Global kill switch
        if is_global_kill_switch_active():
            return False, "Global kill switch active"

        # 2. Lead stopped or status invalid
        if lead.is_stopped:
            return False, f"Lead stopped: {lead.stopped_reason or 'unknown'}"

        if lead.status in (
            LeadStatus.REPLIED,
            LeadStatus.ESCALATED,
            LeadStatus.HUMAN_ENGAGED,
            LeadStatus.CONVERTED,
            LeadStatus.NOT_INTERESTED,
            LeadStatus.UNSUBSCRIBED,
            LeadStatus.PAUSED,
            LeadStatus.LOST,
        ):
            return False, f"Lead in terminal/human status: {lead.status.value}"

        # 3. Campaign active check
        campaign = lead.campaign
        if not campaign or campaign.status != CampaignStatus.ACTIVE:
            return False, f"Campaign is not active (status: {campaign.status if campaign else 'none'})"

        # 4. Campaign daily send limit
        if campaign.daily_sends_today >= campaign.daily_send_limit:
            return False, f"Campaign daily send limit reached ({campaign.daily_sends_today}/{campaign.daily_send_limit})"

        # 5. Prospect unsubscribe / email check
        prospect = lead.prospect
        if not prospect:
            return False, "Lead has no associated prospect"

        if prospect.is_unsubscribed:
            return False, "Prospect is unsubscribed"

        if not prospect.email:
            return False, "Prospect has no email address"

        # 6. Suppression check
        domain = prospect.email.split("@")[-1] if "@" in prospect.email else None
        if await self.is_suppressed(prospect.email, domain):
            return False, f"Email or domain suppressed ({prospect.email})"

        # 7. Verification requirement check
        if campaign.require_email_verification and not prospect.email_verified:
            # High confidence (>0.7) allowed even if not strictly verified
            conf = prospect.email_confidence or 0.0
            if conf < 0.7:
                return False, f"Email not verified and low confidence ({conf:.2f})"

        return True, "OK"

    async def unsubscribe_prospect(self, email_or_id: str, reason: str = "user_request") -> bool:
        """Mark prospect as unsubscribed and stop all active leads."""
        stmt = select(Prospect)
        try:
            p_uuid = uuid.UUID(email_or_id)
            stmt = stmt.where(Prospect.id == p_uuid)
        except ValueError:
            stmt = stmt.where(Prospect.email == email_or_id.lower().strip())

        result = await self._db.execute(stmt)
        prospect = result.scalar_one_or_none()
        if not prospect:
            return False

        prospect.is_unsubscribed = True
        prospect.unsubscribed_at = datetime.now(UTC)

        # Add to suppression list
        if prospect.email:
            existing_sup = await self._db.execute(
                select(Suppression).where(
                    Suppression.suppression_type == "email",
                    Suppression.value == prospect.email.lower().strip(),
                )
            )
            if not existing_sup.scalar_one_or_none():
                self._db.add(Suppression(
                    id=uuid.uuid4(),
                    suppression_type="email",
                    value=prospect.email.lower().strip(),
                    reason=f"Unsubscribed: {reason}",
                ))

        # Stop all active leads for this prospect
        leads_res = await self._db.execute(
            select(Lead).where(Lead.prospect_id == prospect.id)
        )
        for lead in leads_res.scalars().all():
            lead.is_stopped = True
            lead.stopped_reason = "unsubscribed"
            lead.status = LeadStatus.UNSUBSCRIBED

        await self._db.commit()
        logger.info(f"Unsubscribed prospect {prospect.email}")
        return True
