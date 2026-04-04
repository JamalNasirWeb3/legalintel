"""
Pakistani news and media scraper.
Searches major Pakistani news outlets for mentions of the subject.

Sources:
 - Dawn (dawn.com)
 - Geo News (geo.tv)
 - The News International (thenews.com.pk)
 - Express Tribune (tribune.com.pk)
 - ARY News (arynews.tv)
 - Jang (jang.com.pk) — Urdu
 - The Nation (nation.com.pk)
 - Business Recorder (brecorder.com) — financial/business news
"""

import asyncio
import httpx
import re
from scrapers.base import BaseScraper

NEWS_SITES = [
    {"name": "Dawn",               "domain": "dawn.com"},
    {"name": "Geo News",           "domain": "geo.tv"},
    {"name": "The News International", "domain": "thenews.com.pk"},
    {"name": "Express Tribune",    "domain": "tribune.com.pk"},
    {"name": "ARY News",           "domain": "arynews.tv"},
    {"name": "Jang",               "domain": "jang.com.pk"},
    {"name": "The Nation",         "domain": "nation.com.pk"},
    {"name": "Business Recorder",  "domain": "brecorder.com"},
]


class PakistanNewsScraper(BaseScraper):

    async def scrape(self, params: dict) -> dict:
        full_name = params.get("full_name", "")
        keywords = params.get("keywords", "")  # e.g. "fraud", "court", "arrest"

        if not full_name:
            return self._unavailable("Pakistan News", "full_name is required")

        results = []

        # Search all news sites in parallel
        site_results = await asyncio.gather(
            *[self._search_site(full_name, site, keywords) for site in NEWS_SITES],
            return_exceptions=True,
        )
        for found in site_results:
            if isinstance(found, list):
                results.extend(found)

        if not results:
            return self._no_results("Pakistan News Media")

        return self._ok("Pakistan News Media", results)

    async def _search_site(self, full_name: str, site: dict, keywords: str) -> list[dict]:
        """Search a single news site via DuckDuckGo site: search."""
        try:
            query = f'"{full_name}" site:{site["domain"]}'
            if keywords:
                query += f" {keywords}"

            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                resp = await client.get(
                    "https://html.duckduckgo.com/html/",
                    params={"q": query},
                    headers={"User-Agent": "Mozilla/5.0 (compatible; LegalIntelligenceBot/1.0)"},
                )

            if resp.status_code != 200:
                return []

            # Extract result links and titles
            links = re.findall(
                rf'href="(https?://[^"]*{re.escape(site["domain"])}[^"]*)"',
                resp.text
            )
            # Try to extract surrounding text snippets
            snippets = re.findall(r'<a class="result__snippet"[^>]*>(.*?)</a>', resp.text)

            results = []
            for i, link in enumerate(links[:4]):
                result = {
                    "source": site["name"],
                    "url": link,
                    "subject_mentioned": full_name,
                }
                if i < len(snippets):
                    # Strip HTML tags from snippet
                    result["snippet"] = re.sub(r'<[^>]+>', '', snippets[i]).strip()
                results.append(result)

            return results

        except Exception:
            return []
