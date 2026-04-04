"""
Court records scraper using the CourtListener REST API (free, no auth required for basic search).
CourtListener aggregates PACER federal court data and many state courts.
API docs: https://www.courtlistener.com/api/rest/v4/
"""

import httpx
from scrapers.base import BaseScraper

COURTLISTENER_BASE = "https://www.courtlistener.com/api/rest/v4"


class CourtRecordsScraper(BaseScraper):

    async def scrape(self, params: dict) -> dict:
        full_name = params.get("full_name", "")
        state = params.get("state", "")

        if not full_name:
            return self._unavailable("CourtListener", "full_name is required")

        try:
            results = []

            async with httpx.AsyncClient(timeout=30) as client:
                # Search for docket entries by party name
                resp = await client.get(
                    f"{COURTLISTENER_BASE}/dockets/",
                    params={
                        "party_name": full_name,
                        "fields": "id,case_name,court,date_filed,docket_number,pacer_case_id,absolute_url",
                        "page_size": 20,
                    },
                    headers={"Accept": "application/json"},
                )
                resp.raise_for_status()
                data = resp.json()

                for docket in data.get("results", []):
                    results.append({
                        "source": "CourtListener / PACER",
                        "case_name": docket.get("case_name"),
                        "docket_number": docket.get("docket_number"),
                        "court": docket.get("court"),
                        "date_filed": docket.get("date_filed"),
                        "url": f"https://www.courtlistener.com{docket.get('absolute_url', '')}",
                    })

            if not results:
                return self._no_results("CourtListener")

            return self._ok("CourtListener", results)

        except httpx.HTTPStatusError as e:
            return self._unavailable("CourtListener", f"HTTP {e.response.status_code}")
        except Exception as e:
            return self._unavailable("CourtListener", str(e))
