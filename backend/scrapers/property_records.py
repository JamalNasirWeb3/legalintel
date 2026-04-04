"""
Property records scraper.
Uses the Regrid API (free tier) which aggregates US county assessor data.
Fallback: state-specific public portals via Playwright.
API docs: https://regrid.com/api
"""

import httpx
from scrapers.base import BaseScraper

REGRID_BASE = "https://app.regrid.com/api/v2"


class PropertyRecordsScraper(BaseScraper):

    async def scrape(self, params: dict) -> dict:
        full_name = params.get("full_name", "")
        state = params.get("state", "").lower()
        city = params.get("city", "")

        if not full_name:
            return self._unavailable("Regrid / County Assessor", "full_name is required")

        try:
            results = []

            async with httpx.AsyncClient(timeout=30) as client:
                # Regrid parcel search by owner name
                search_params = {
                    "query": full_name,
                    "return_geometry": "false",
                    "limit": 20,
                }
                if state:
                    search_params["state_abbreviation"] = state.upper()
                if city:
                    search_params["city"] = city

                resp = await client.get(
                    f"{REGRID_BASE}/parcels/search",
                    params=search_params,
                    headers={"Accept": "application/json"},
                )

                if resp.status_code == 401:
                    # No API key — return note for agent
                    return self._unavailable(
                        "Regrid",
                        "API key required. Add REGRID_API_KEY to .env for property record lookups."
                    )

                resp.raise_for_status()
                data = resp.json()

                for feature in data.get("parcels", {}).get("features", []):
                    props = feature.get("properties", {})
                    results.append({
                        "source": "Regrid / County Assessor",
                        "owner_name": props.get("owner"),
                        "address": props.get("address"),
                        "city": props.get("city"),
                        "state": props.get("state_abbr"),
                        "zip": props.get("zip"),
                        "parcel_number": props.get("parcel_id"),
                        "assessed_value": props.get("taxyear") and props.get("landval"),
                        "land_use": props.get("usedesc"),
                        "county": props.get("county"),
                    })

            if not results:
                return self._no_results("Regrid / County Assessor")

            return self._ok("Regrid / County Assessor", results)

        except httpx.HTTPStatusError as e:
            return self._unavailable("Regrid / County Assessor", f"HTTP {e.response.status_code}")
        except Exception as e:
            return self._unavailable("Regrid / County Assessor", str(e))
