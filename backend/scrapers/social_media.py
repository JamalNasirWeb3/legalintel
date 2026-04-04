"""
Social media scraper for public profiles.
Uses web search (via httpx + DuckDuckGo HTML) to find public profile URLs,
then Playwright to extract publicly visible profile data.
No authentication — public data only.
"""

import re
import httpx
from scrapers.base import BaseScraper


class SocialMediaScraper(BaseScraper):

    PLATFORMS = ["linkedin.com/in/", "twitter.com/", "x.com/", "facebook.com/"]

    async def scrape(self, params: dict) -> dict:
        full_name = params.get("full_name", "")
        city = params.get("city", "")
        employer = params.get("employer", "")

        if not full_name:
            return self._unavailable("Social Media Search", "full_name is required")

        try:
            results = []
            query_parts = [f'"{full_name}"']
            if city:
                query_parts.append(city)
            if employer:
                query_parts.append(employer)

            for platform_key in ["linkedin", "twitter OR x.com"]:
                query = " ".join(query_parts) + f" site:{platform_key}.com" if "linkedin" in platform_key else " ".join(query_parts) + " (site:twitter.com OR site:x.com)"
                found = await self._duckduckgo_search(query, platform_key)
                results.extend(found)

            if not results:
                return self._no_results("Social Media (DuckDuckGo)")

            return self._ok("Social Media (DuckDuckGo)", results)

        except Exception as e:
            return self._unavailable("Social Media Search", str(e))

    async def _duckduckgo_search(self, query: str, platform: str) -> list[dict]:
        """Search DuckDuckGo HTML endpoint and parse result links."""
        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                resp = await client.get(
                    "https://html.duckduckgo.com/html/",
                    params={"q": query},
                    headers={
                        "User-Agent": "Mozilla/5.0 (compatible; LegalIntelligenceBot/1.0; public record research)"
                    },
                )
                resp.raise_for_status()

            # Extract result links from HTML
            links = re.findall(r'href="(https?://[^"]+)"', resp.text)
            profile_links = [
                l for l in links
                if any(p in l for p in self.PLATFORMS)
            ]

            results = []
            for link in profile_links[:5]:  # limit to top 5 per platform
                results.append({
                    "source": f"Social Media / {platform}",
                    "profile_url": link,
                    "note": "Public profile — verify manually",
                })

            return results

        except Exception:
            return []
