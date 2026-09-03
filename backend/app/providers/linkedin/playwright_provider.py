"""
LinkedIn Playwright browser automation provider.

IMPORTANT DESIGN PRINCIPLES:
- LinkedIn automation is OPTIONAL. The rest of the system works fully without it.
- We use authenticated session cookies (li_at), never stored passwords.
- All actions use human-like timing and conservative rate limits.
- We do NOT attempt to bypass CAPTCHAs, 2FA, or security controls.
- We do NOT automate connection requests or messages on LinkedIn.
- This provider is READ-ONLY for prospect research only.
"""

from __future__ import annotations

import asyncio
import logging
import random
from contextlib import asynccontextmanager

from app.providers.base import LinkedInProfile, LinkedInProvider

logger = logging.getLogger(__name__)


class PlaywrightLinkedInProvider:
    """
    Read-only LinkedIn profile research via Playwright.
    Uses an authenticated session cookie — no password storage.
    """

    provider_name = "linkedin_playwright"
    is_enabled: bool

    def __init__(
        self,
        session_cookie: str,
        rate_limit_per_hour: int = 20,
        delay_min_ms: int = 2000,
        delay_max_ms: int = 8000,
        enabled: bool = False,
    ):
        self.is_enabled = enabled
        self._session_cookie = session_cookie
        self._rate_limit = rate_limit_per_hour
        self._delay_min = delay_min_ms / 1000
        self._delay_max = delay_max_ms / 1000
        self._request_count = 0
        self._playwright = None
        self._browser = None

    async def _human_delay(self):
        """Simulate human reading/thinking time."""
        await asyncio.sleep(random.uniform(self._delay_min, self._delay_max))

    @asynccontextmanager
    async def _get_page(self):
        """Create a browser page with LinkedIn session cookie."""
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise RuntimeError("Playwright is not installed. Run: pip install playwright && playwright install chromium")

        if not self._playwright:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=True)

        context = await self._browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )
        await context.add_cookies([
            {
                "name": "li_at",
                "value": self._session_cookie,
                "domain": ".linkedin.com",
                "path": "/",
            }
        ])
        page = await context.new_page()
        try:
            yield page
        finally:
            await context.close()

    async def search_people(
        self,
        query: str,
        filters: dict | None = None,
    ) -> list[LinkedInProfile]:
        if not self.is_enabled:
            logger.info("LinkedIn provider is disabled. Skipping search.")
            return []
        if self._request_count >= self._rate_limit:
            logger.warning("LinkedIn rate limit reached for this hour.")
            return []

        results = []
        try:
            async with self._get_page() as page:
                url = f"https://www.linkedin.com/search/results/people/?keywords={query}"
                await page.goto(url, wait_until="domcontentloaded")
                await self._human_delay()
                self._request_count += 1

                cards = await page.query_selector_all(".entity-result")
                for card in cards[:10]:
                    try:
                        name_el = await card.query_selector(".entity-result__title-text")
                        name = (await name_el.inner_text()).strip() if name_el else ""
                        subtitle_el = await card.query_selector(".entity-result__primary-subtitle")
                        headline = (await subtitle_el.inner_text()).strip() if subtitle_el else ""
                        link_el = await card.query_selector("a.app-aware-link")
                        profile_url = await link_el.get_attribute("href") if link_el else ""
                        if name:
                            results.append(
                                LinkedInProfile(
                                    url=profile_url or "",
                                    full_name=name,
                                    headline=headline,
                                    location="",
                                )
                            )
                    except Exception:
                        continue
        except Exception as e:
            logger.error(f"LinkedIn search failed: {e}")

        return results

    async def get_profile(self, url: str) -> LinkedInProfile | None:
        if not self.is_enabled:
            return None
        if self._request_count >= self._rate_limit:
            logger.warning("LinkedIn rate limit reached.")
            return None

        try:
            async with self._get_page() as page:
                await page.goto(url, wait_until="domcontentloaded")
                await self._human_delay()
                self._request_count += 1

                name_el = await page.query_selector("h1.text-heading-xlarge")
                name = (await name_el.inner_text()).strip() if name_el else ""
                headline_el = await page.query_selector(".text-body-medium.break-words")
                headline = (await headline_el.inner_text()).strip() if headline_el else ""
                location_el = await page.query_selector(".text-body-small.inline")
                location = (await location_el.inner_text()).strip() if location_el else ""
                about_el = await page.query_selector(".display-flex.ph5.pv3")
                about = (await about_el.inner_text()).strip() if about_el else ""

                return LinkedInProfile(
                    url=url,
                    full_name=name,
                    headline=headline,
                    location=location,
                    about=about,
                )
        except Exception as e:
            logger.error(f"LinkedIn profile fetch failed: {e}")
            return None

    async def health_check(self) -> bool:
        if not self.is_enabled:
            return True  # Disabled = not broken
        try:
            async with self._get_page() as page:
                await page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")
                return "linkedin.com" in page.url
        except Exception as e:
            logger.error(f"LinkedIn health check failed: {e}")
            return False

    async def close(self):
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()


class DisabledLinkedInProvider:
    """Stub provider used when LinkedIn is disabled."""

    provider_name = "linkedin_disabled"
    is_enabled = False

    async def search_people(self, query: str, filters=None) -> list:
        return []

    async def get_profile(self, url: str) -> None:
        return None

    async def health_check(self) -> bool:
        return True
