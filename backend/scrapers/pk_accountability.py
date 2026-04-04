"""
Pakistani accountability, criminal, and special-court records scraper.

Uses DuckDuckGo site-targeted searches because NAB, FIA, ATC, and district
court portals have no public REST APIs and block automated browsers.

Sources covered:
  - NAB  (National Accountability Bureau)   nab.gov.pk
  - FIA  (Federal Investigation Agency)     fia.gov.pk
  - Accountability Courts                   (via news + court sites)
  - Anti-Terrorism Courts (ATC)             (via news)
  - e-Courts Pakistan                       ecourts.gov.pk
  - District / Sessions Courts              districtcourts.gov.pk
  - Supreme Court & High Court judgments    (site: search fallback)
  - Pakistan legal databases                pakistanlawsite.com, plj.com.pk
  - FIR / criminal record mentions          (general search)
"""

import asyncio
import re
import httpx
from scrapers.base import BaseScraper


# Each entry: label shown in results + list of DDG query templates.
# {name} is replaced with the subject's full name at runtime.
_SEARCH_GROUPS = [
    {
        "label": "NAB (National Accountability Bureau)",
        "queries": [
            '"{name}" site:nab.gov.pk',
            '"{name}" NAB "reference" OR "NAB case" OR "conviction" Pakistan',
            '"{name}" "national accountability" OR "NAB court" Pakistan',
        ],
    },
    {
        "label": "FIA (Federal Investigation Agency)",
        "queries": [
            '"{name}" site:fia.gov.pk',
            '"{name}" FIA Pakistan "case" OR "arrested" OR "investigation" OR "wanted"',
        ],
    },
    {
        "label": "Accountability Court",
        "queries": [
            '"{name}" "accountability court" Pakistan',
            '"{name}" "NAB reference" OR "accountability court" verdict Pakistan',
        ],
    },
    {
        "label": "Anti-Terrorism Court (ATC)",
        "queries": [
            '"{name}" "anti-terrorism court" OR "ATC" Pakistan',
            '"{name}" "terrorism" court Pakistan',
        ],
    },
    {
        "label": "e-Courts Pakistan",
        "queries": [
            '"{name}" site:ecourts.gov.pk',
        ],
    },
    {
        "label": "High Court & Supreme Court Judgments",
        "queries": [
            '"{name}" site:supremecourt.gov.pk',
            '"{name}" site:lhc.gov.pk OR site:ihc.gov.pk OR site:shc.gov.pk OR site:peshawarhighcourt.com.pk',
            '"{name}" "judgment" "petitioner" OR "respondent" Pakistan court',
        ],
    },
    {
        "label": "District / Sessions Court",
        "queries": [
            '"{name}" site:districtcourts.gov.pk',
            '"{name}" "sessions court" OR "district court" Pakistan',
        ],
    },
    {
        "label": "FIR & Criminal Record",
        "queries": [
            '"{name}" "FIR" Pakistan police',
            '"{name}" "arrested" OR "detained" OR "convicted" OR "sentenced" Pakistan',
            '"{name}" "bail" court Pakistan',
        ],
    },
    {
        "label": "Pakistan Legal Judgments (PLD / PLJ)",
        "queries": [
            '"{name}" site:pakistanlawsite.com OR site:plj.com.pk',
            '"{name}" "PLD" OR "PLJ" Pakistan court judgment',
        ],
    },
]

_DDG_URL = "https://html.duckduckgo.com/html/"
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; LegalIntelligenceBot/1.0)"}
_MAX_RESULTS_PER_QUERY = 5


class PakistanAccountabilityScraper(BaseScraper):
    """Search NAB, FIA, ATC, accountability courts, e-Courts, and criminal records."""

    async def scrape(self, params: dict) -> dict:
        full_name = params.get("full_name", "").strip()
        keywords = params.get("keywords", "").strip()

        if not full_name:
            return self._unavailable("Pakistan Accountability / Criminal Records", "full_name is required")

        all_results: list[dict] = []
        seen_urls: set[str] = set()

        async with httpx.AsyncClient(
            timeout=20.0,
            follow_redirects=True,
            headers=_HEADERS,
        ) as client:
            tasks = []
            for group in _SEARCH_GROUPS:
                for query_tpl in group["queries"]:
                    q = query_tpl.format(name=full_name)
                    if keywords:
                        q += f" {keywords}"
                    tasks.append(self._ddg_search(client, q, group["label"], seen_urls))

            batches = await asyncio.gather(*tasks, return_exceptions=True)

        for batch in batches:
            if isinstance(batch, list):
                all_results.extend(batch)

        if not all_results:
            return self._no_results("Pakistan Accountability / Criminal Records")

        return self._ok("Pakistan Accountability / Criminal Records", all_results)

    async def _ddg_search(
        self,
        client: httpx.AsyncClient,
        query: str,
        label: str,
        seen_urls: set,
    ) -> list[dict]:
        try:
            resp = await client.get(_DDG_URL, params={"q": query})
            if resp.status_code != 200:
                return []

            # Extract result links
            links = re.findall(r'href="(https?://[^"]{10,})"', resp.text)
            # Extract text snippets
            snippets = re.findall(
                r'class="result__snippet"[^>]*>(.*?)</a>', resp.text, re.DOTALL
            )

            results = []
            snippet_idx = 0
            for link in links:
                # Skip DuckDuckGo internal links
                if "duckduckgo.com" in link or "duck.co" in link:
                    continue
                if link in seen_urls:
                    continue
                if len(results) >= _MAX_RESULTS_PER_QUERY:
                    break

                seen_urls.add(link)
                entry: dict = {
                    "source": label,
                    "url": link,
                    "query_used": query,
                }
                if snippet_idx < len(snippets):
                    clean = re.sub(r"<[^>]+>", "", snippets[snippet_idx]).strip()
                    if clean:
                        entry["snippet"] = clean[:300]
                    snippet_idx += 1

                results.append(entry)

            return results

        except Exception:
            return []
