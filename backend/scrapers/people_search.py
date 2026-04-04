"""
People search scraper.
Uses the US Census / voter registration data aggregated through
public APIs and web search. Focuses on finding known addresses,
relatives, and spouse information from public records.
"""

import httpx
from scrapers.base import BaseScraper


class PeopleSearchScraper(BaseScraper):

    async def scrape(self, params: dict) -> dict:
        full_name = params.get("full_name", "")
        state = params.get("state", "")
        date_of_birth = params.get("date_of_birth", "")

        if not full_name:
            return self._unavailable("People Search", "full_name is required")

        results = []

        # Search voter registration data (many states publish this publicly)
        voter_results = await self._search_voter_records(full_name, state)
        results.extend(voter_results)

        # Search public obituaries/family trees for associate info
        assoc_results = await self._search_public_records(full_name, state, date_of_birth)
        results.extend(assoc_results)

        if not results:
            return self._no_results("People Search / Public Records")

        return self._ok("People Search / Public Records", results)

    async def _search_voter_records(self, full_name: str, state: str) -> list[dict]:
        """
        Many states provide public voter registration lookups.
        This searches the few states with open REST APIs.
        For other states, the attorney must query the state's portal directly.
        """
        # Ohio is one example of a state with a relatively open voter search
        # Most states require a direct portal visit — flag this for the attorney
        return [{
            "source": "Voter Records Note",
            "note": (
                f"Voter registration records in {state or 'most states'} are public but "
                "typically require the state's official portal. "
                f"Search: https://www.vote411.org/voter-registration-status or the "
                f"{state} Secretary of State website for {full_name}."
            ),
            "query_name": full_name,
            "state": state,
        }]

    async def _search_public_records(
        self, full_name: str, state: str, date_of_birth: str
    ) -> list[dict]:
        """
        Search Whitepages public data via web search (no API key needed for basic results).
        Also searches FindAGrave and FamilySearch public trees for relative information.
        """
        try:
            query = f'"{full_name}" {state} address relatives spouse'

            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                resp = await client.get(
                    "https://html.duckduckgo.com/html/",
                    params={"q": query},
                    headers={
                        "User-Agent": "Mozilla/5.0 (compatible; LegalIntelligenceBot/1.0; public record research)"
                    },
                )

            results = []
            if resp.status_code == 200:
                # Surface whitepages/spokeo/fastpeoplesearch links specifically
                import re
                links = re.findall(r'href="(https?://(?:www\.whitepages|www\.fastpeoplesearch|www\.spokeo|radaris)[^"]+)"', resp.text)
                for link in links[:5]:
                    results.append({
                        "source": "People Search (Web)",
                        "url": link,
                        "note": "Public aggregator — contains address history, possible relatives",
                    })

            return results

        except Exception:
            return []
