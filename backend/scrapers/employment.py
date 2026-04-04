"""
Employment scraper.
Searches professional license databases (which are public records) and
web-search-derived LinkedIn public profile data.
"""

import httpx
from scrapers.base import BaseScraper


# State professional license lookup APIs (free, public)
# Many states publish license data via their own open data portals
LICENSE_APIS = {
    "CA": "https://api.dol.gov/V1/ProfessionalLicenses",  # placeholder — replace with state-specific
    # Add more state-specific endpoints as needed
}


class EmploymentScraper(BaseScraper):

    async def scrape(self, params: dict) -> dict:
        full_name = params.get("full_name", "")
        state = params.get("state", "").upper()
        occupation = params.get("occupation", "")

        if not full_name:
            return self._unavailable("Employment / License Search", "full_name is required")

        results = []

        # Try state professional license search
        license_results = await self._search_licenses(full_name, state)
        results.extend(license_results)

        # Try web search for public employment info
        web_results = await self._web_search_employment(full_name, state, occupation)
        results.extend(web_results)

        if not results:
            return self._no_results("Employment / License Databases")

        return self._ok("Employment / License Databases", results)

    async def _search_licenses(self, full_name: str, state: str) -> list[dict]:
        """Search NPPES (National Provider Index) for healthcare providers — fully public."""
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                # NPPES NPI Registry is a free, open federal database
                resp = await client.get(
                    "https://npiregistry.cms.hhs.gov/api/",
                    params={
                        "version": "2.1",
                        "first_name": full_name.split()[0] if full_name.split() else "",
                        "last_name": full_name.split()[-1] if full_name.split() else "",
                        "state": state,
                        "limit": 10,
                    },
                    headers={"Accept": "application/json"},
                )
                resp.raise_for_status()
                data = resp.json()

                results = []
                for provider in data.get("results", []):
                    basic = provider.get("basic", {})
                    addresses = provider.get("addresses", [])
                    practice_addr = next((a for a in addresses if a.get("address_purpose") == "LOCATION"), {})

                    results.append({
                        "source": "NPPES NPI Registry (Federal)",
                        "npi": provider.get("number"),
                        "name": f"{basic.get('first_name', '')} {basic.get('last_name', '')}".strip(),
                        "credential": basic.get("credential"),
                        "taxonomy": provider.get("taxonomies", [{}])[0].get("desc"),
                        "employer": practice_addr.get("organization_name"),
                        "city": practice_addr.get("city"),
                        "state": practice_addr.get("state"),
                        "status": basic.get("status"),
                    })

                return results

        except Exception:
            return []

    async def _web_search_employment(self, full_name: str, state: str, occupation: str) -> list[dict]:
        """Use web search to find employment info from public sources."""
        try:
            query = f'"{full_name}" {state} employer OR "works at" OR "employed by"'
            if occupation:
                query += f" {occupation}"

            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                resp = await client.get(
                    "https://html.duckduckgo.com/html/",
                    params={"q": query},
                    headers={
                        "User-Agent": "Mozilla/5.0 (compatible; LegalIntelligenceBot/1.0; public record research)"
                    },
                )

            if resp.status_code != 200:
                return []

            # Return note that web search was attempted
            return [{
                "source": "Web Search (employment)",
                "query": query,
                "note": "Web search attempted — review public sources manually for specific employment details",
                "status": "searched",
            }]

        except Exception:
            return []
