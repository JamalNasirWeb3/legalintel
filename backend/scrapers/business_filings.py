"""
Business filings scraper using the OpenCorporates API (free tier).
Covers most US states and many international jurisdictions.
API docs: https://api.opencorporates.com/documentation/API-Reference
"""

import httpx
from scrapers.base import BaseScraper

OPENCORPORATES_BASE = "https://api.opencorporates.com/v0.4"


class BusinessFilingsScraper(BaseScraper):

    async def scrape(self, params: dict) -> dict:
        full_name = params.get("full_name", "")
        state = params.get("state", "").lower()

        if not full_name:
            return self._unavailable("OpenCorporates", "full_name is required")

        try:
            results = []
            jurisdiction = f"us_{state}" if state else None

            async with httpx.AsyncClient(timeout=30) as client:
                # Search officers (people associated with companies)
                officer_params = {
                    "q": full_name,
                    "fields": "name,company,position,start_date,end_date",
                    "per_page": 20,
                }
                if jurisdiction:
                    officer_params["jurisdiction_code"] = jurisdiction

                resp = await client.get(
                    f"{OPENCORPORATES_BASE}/officers/search",
                    params=officer_params,
                    headers={"Accept": "application/json"},
                )
                resp.raise_for_status()
                data = resp.json()

                for item in data.get("results", {}).get("officers", []):
                    officer = item.get("officer", {})
                    company = officer.get("company", {})
                    results.append({
                        "source": "OpenCorporates",
                        "person_name": officer.get("name"),
                        "position": officer.get("position"),
                        "company_name": company.get("name"),
                        "company_number": company.get("company_number"),
                        "jurisdiction": company.get("jurisdiction_code"),
                        "company_status": company.get("current_status"),
                        "start_date": officer.get("start_date"),
                        "end_date": officer.get("end_date"),
                        "url": company.get("opencorporates_url"),
                    })

            if not results:
                return self._no_results("OpenCorporates")

            return self._ok("OpenCorporates", results)

        except httpx.HTTPStatusError as e:
            return self._unavailable("OpenCorporates", f"HTTP {e.response.status_code}")
        except Exception as e:
            return self._unavailable("OpenCorporates", str(e))
