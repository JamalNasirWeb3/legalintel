"""
Pakistan-focused social media scraper.
Searches public profiles on major platforms with Pakistan-specific context.

Platforms:
 - Facebook public pages/profiles
 - X / Twitter public profiles
 - LinkedIn public profiles
 - Instagram public profiles
 - YouTube channels
 - TikTok (widely used in Pakistan)
"""

import asyncio
import httpx
import re
from scrapers.base import BaseScraper

PLATFORMS = [
    {"name": "LinkedIn",  "domain": "linkedin.com/in/"},
    {"name": "Twitter/X", "domain": "twitter.com/"},
    {"name": "Twitter/X", "domain": "x.com/"},
    {"name": "Facebook",  "domain": "facebook.com/"},
    {"name": "Instagram", "domain": "instagram.com/"},
    {"name": "YouTube",   "domain": "youtube.com/"},
    {"name": "TikTok",    "domain": "tiktok.com/@"},
]


class PakistanSocialMediaScraper(BaseScraper):

    async def scrape(self, params: dict) -> dict:
        full_name = params.get("full_name", "")
        city = params.get("city", "")
        employer = params.get("employer", "")

        if not full_name:
            return self._unavailable("Pakistan Social Media", "full_name is required")

        results = []

        # Build context-aware queries
        queries = [
            f'"{full_name}" Pakistan',
            f'"{full_name}" Pakistan (site:linkedin.com OR site:twitter.com OR site:x.com)',
            f'"{full_name}" Pakistan (site:facebook.com OR site:instagram.com)',
        ]
        if city:
            queries.append(f'"{full_name}" {city} Pakistan')
        if employer:
            queries.append(f'"{full_name}" "{employer}" Pakistan')

        seen_urls = set()
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            all_found = await asyncio.gather(
                *[self._ddg_search(client, query, seen_urls) for query in queries],
                return_exceptions=True,
            )
            for found in all_found:
                if isinstance(found, list):
                    results.extend(found)

        if not results:
            return self._no_results("Pakistan Social Media")

        return self._ok("Pakistan Social Media", results)

    async def _ddg_search(self, client: httpx.AsyncClient, query: str, seen_urls: set) -> list[dict]:
        try:
            resp = await client.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers={"User-Agent": "Mozilla/5.0 (compatible; LegalIntelligenceBot/1.0)"},
            )
            if resp.status_code != 200:
                return []

            links = re.findall(r'href="(https?://[^"]+)"', resp.text)
            results = []
            for link in links:
                if link in seen_urls:
                    continue
                platform = next(
                    (p for p in PLATFORMS if p["domain"] in link),
                    None
                )
                if platform:
                    seen_urls.add(link)
                    results.append({
                        "source": f"Social Media / {platform['name']}",
                        "platform": platform["name"],
                        "profile_url": link,
                        "context": "Pakistan",
                        "note": "Public profile — verify manually",
                    })
            return results[:6]

        except Exception:
            return []
