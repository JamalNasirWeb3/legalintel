"""
Pakistani business registry scrapers using Playwright.

Sources:
 - SECP company search     secp.gov.pk/companies-search/
 - OpenCorporates Pakistan api.opencorporates.com (REST, no browser needed)
 - FBR Active Taxpayer List fbr.gov.pk (ATL file download — referenced only)
"""

import asyncio
import httpx
import re
from playwright.async_api import async_playwright, TimeoutError as PWTimeout
from scrapers.base import BaseScraper

HEADLESS = True
TIMEOUT = 25_000
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
OPENCORPORATES_BASE = "https://api.opencorporates.com/v0.4"


class PakistanBusinessScraper(BaseScraper):

    async def scrape(self, params: dict) -> dict:
        full_name = params.get("full_name", "")
        company_name = params.get("company_name", "")
        search_term = company_name or full_name

        if not search_term:
            return self._unavailable("Pakistan Business Registry", "full_name or company_name required")

        results = []

        # Run SECP (Playwright) and OpenCorporates (REST) in parallel
        secp_results, oc_results = await asyncio.gather(
            self._search_secp(search_term, full_name),
            self._search_opencorporates(full_name, company_name),
            return_exceptions=True,
        )

        if isinstance(secp_results, list):
            results.extend(secp_results)
        if isinstance(oc_results, list):
            results.extend(oc_results)

        # FBR reference note (ATL is a downloadable Excel file — no automated search)
        results.append({
            "source": "FBR Active Taxpayer List",
            "note": (
                f"Verify '{search_term}' on FBR ATL at https://www.fbr.gov.pk/atl-income-tax/131052 "
                "or NTN verification at https://e.fbr.gov.pk"
            ),
            "action_required": True,
        })

        if not results:
            return self._no_results("Pakistan Business Registry")

        return self._ok("Pakistan Business Registry", results)

    async def _search_secp(self, search_term: str, officer_name: str) -> list[dict]:
        """Scrape SECP company search with Playwright."""
        results = []
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=HEADLESS)
            page = await browser.new_page(user_agent=USER_AGENT)
            try:
                await page.goto(
                    "https://www.secp.gov.pk/companies-search/",
                    timeout=TIMEOUT,
                    wait_until="domcontentloaded",
                )

                # Look for the search input
                search_input = page.locator(
                    "input[type='search'], input[name='s'], input[type='text'], input[name*='search'], input[placeholder*='company']"
                ).first

                if await search_input.count() > 0:
                    await search_input.fill(search_term)
                    await page.keyboard.press("Enter")
                    await page.wait_for_load_state("networkidle", timeout=TIMEOUT)

                    # Extract results table
                    rows = await page.locator("table tbody tr, .company-result, .search-result").all()
                    for row in rows[:15]:
                        text = (await row.inner_text()).strip()
                        if text and len(text) > 5:
                            results.append({
                                "source": "SECP (Securities & Exchange Commission of Pakistan)",
                                "record": text[:400],
                                "url": "https://www.secp.gov.pk/companies-search/",
                                "search_term": search_term,
                            })

                    if not results:
                        # Check page text for any mention
                        content = await page.inner_text("body")
                        if search_term.split()[0].lower() in content.lower():
                            results.append({
                                "source": "SECP",
                                "note": f"'{search_term}' found on SECP search — review manually",
                                "url": page.url,
                            })
                else:
                    results.append({
                        "source": "SECP",
                        "note": "Search input not found — SECP site structure may have changed. Visit secp.gov.pk/companies-search/ manually.",
                    })

            except PWTimeout:
                results.append({"source": "SECP", "note": "Timed out — visit secp.gov.pk/companies-search/ manually"})
            except Exception as e:
                results.append({"source": "SECP", "error": str(e)})
            finally:
                await page.close()
                await browser.close()

        return results

    async def _search_opencorporates(self, full_name: str, company_name: str) -> list[dict]:
        """Search OpenCorporates Pakistan jurisdiction via REST API."""
        results = []
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                # Search officers (people associated with companies)
                if full_name:
                    resp = await client.get(
                        f"{OPENCORPORATES_BASE}/officers/search",
                        params={"q": full_name, "jurisdiction_code": "pk", "per_page": 10},
                        headers={"Accept": "application/json"},
                    )
                    if resp.status_code == 200:
                        for item in resp.json().get("results", {}).get("officers", []):
                            officer = item.get("officer", {})
                            company = officer.get("company", {})
                            results.append({
                                "source": "OpenCorporates Pakistan",
                                "person_name": officer.get("name"),
                                "position": officer.get("position"),
                                "company_name": company.get("name"),
                                "company_status": company.get("current_status"),
                                "incorporation_date": company.get("incorporation_date"),
                                "url": company.get("opencorporates_url"),
                            })

                # Search companies by name
                search = company_name or full_name
                resp2 = await client.get(
                    f"{OPENCORPORATES_BASE}/companies/search",
                    params={"q": search, "jurisdiction_code": "pk", "per_page": 10},
                    headers={"Accept": "application/json"},
                )
                if resp2.status_code == 200:
                    for item in resp2.json().get("results", {}).get("companies", []):
                        company = item.get("company", {})
                        results.append({
                            "source": "OpenCorporates Pakistan (Company)",
                            "company_name": company.get("name"),
                            "company_number": company.get("company_number"),
                            "status": company.get("current_status"),
                            "incorporation_date": company.get("incorporation_date"),
                            "url": company.get("opencorporates_url"),
                        })
        except Exception as e:
            results.append({"source": "OpenCorporates Pakistan", "error": str(e)})

        return results
