"""
Pakistani court scrapers using Playwright for JS-rendered court portals.

Courts covered:
 - Lahore High Court       lhc.gov.pk           — case search form
 - Supreme Court           supremecourt.gov.pk   — cause list / judgment search
 - Islamabad High Court    ihc.gov.pk            — case search
 - Sindh High Court        shc.gov.pk            — case status
 - Peshawar High Court     peshawarhighcourt.com.pk
"""

import asyncio
import re
import httpx
from playwright.async_api import async_playwright, TimeoutError as PWTimeout
from scrapers.base import BaseScraper

_DDG_URL = "https://html.duckduckgo.com/html/"
_DDG_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; LegalIntelligenceBot/1.0)"}


async def _ddg_court_search(full_name: str, site_domain: str, court_label: str) -> list[dict]:
    """Fallback: search a court's website via DuckDuckGo when Playwright fails."""
    results = []
    try:
        query = f'"{full_name}" site:{site_domain}'
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, headers=_DDG_HEADERS) as client:
            resp = await client.get(_DDG_URL, params={"q": query})
        if resp.status_code != 200:
            return results
        links = re.findall(
            rf'href="(https?://[^"]*{re.escape(site_domain)}[^"]*)"', resp.text
        )
        snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', resp.text, re.DOTALL)
        for i, link in enumerate(links[:4]):
            entry = {"source": court_label, "url": link, "method": "DDG fallback"}
            if i < len(snippets):
                clean = re.sub(r"<[^>]+>", "", snippets[i]).strip()
                if clean:
                    entry["snippet"] = clean[:300]
            results.append(entry)
    except Exception:
        pass
    return results

HEADLESS = True
TIMEOUT = 20_000   # ms per navigation
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


class PakistanCourtsScraper(BaseScraper):

    async def scrape(self, params: dict) -> dict:
        full_name = params.get("full_name", "")
        province = params.get("province", "").lower()

        if not full_name:
            return self._unavailable("Pakistan Courts", "full_name is required")

        results = []

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=HEADLESS)
            context = await browser.new_context(user_agent=USER_AGENT)

            # Run court searches based on province or all
            tasks = []
            if not province or province in ("punjab", "all"):
                tasks.append(self._search_lhc(context, full_name))
            if not province or province in ("islamabad", "all"):
                tasks.append(self._search_ihc(context, full_name))
            if not province or province in ("sindh", "all"):
                tasks.append(self._search_shc(context, full_name))
            if not province or province in ("kpk", "all"):
                tasks.append(self._search_phc(context, full_name))
            # Supreme Court always searched
            tasks.append(self._search_supreme_court(context, full_name))

            court_results = await asyncio.gather(*tasks, return_exceptions=True)
            for r in court_results:
                if isinstance(r, list):
                    results.extend(r)
                elif isinstance(r, Exception):
                    results.append({"source": "Pakistan Court", "error": str(r)})

            await browser.close()

        if not results:
            return self._no_results("Pakistan Courts")

        return self._ok("Pakistan Courts", results)

    async def _search_lhc(self, context, full_name: str) -> list[dict]:
        """Lahore High Court — case search at lhc.gov.pk"""
        page = await context.new_page()
        results = []
        try:
            await page.goto("https://lhc.gov.pk/case_status", timeout=TIMEOUT, wait_until="domcontentloaded")

            # Try to find a party name search input
            name_input = page.locator("input[name*='party'], input[placeholder*='party'], input[placeholder*='name'], input[id*='party']").first
            if await name_input.count() > 0:
                await name_input.fill(full_name)
                await page.keyboard.press("Enter")
                await page.wait_for_load_state("networkidle", timeout=TIMEOUT)

                # Extract any table rows
                rows = await page.locator("table tr").all()
                for row in rows[1:11]:  # skip header, max 10
                    text = (await row.inner_text()).strip()
                    if text and full_name.split()[0].lower() in text.lower():
                        results.append({
                            "source": "Lahore High Court",
                            "record": text,
                            "url": "https://lhc.gov.pk/case_status",
                        })
            else:
                # Fallback: check if name appears anywhere on the page after search
                content = await page.content()
                if full_name.split()[0].lower() in content.lower():
                    results.append({
                        "source": "Lahore High Court",
                        "note": f"Name '{full_name}' found on LHC case search page",
                        "url": "https://lhc.gov.pk/case_status",
                    })

        except (PWTimeout, Exception):
            pass  # fall through to DDG fallback
        finally:
            await page.close()

        if not results:
            results = await _ddg_court_search(full_name, "lhc.gov.pk", "Lahore High Court")
        return results

    async def _search_lhc_unused(self, *_):  # sentinel to keep indentation clean
        results = []
        try:
            pass
        finally:
            await page.close()
        return results

    async def _search_ihc(self, context, full_name: str) -> list[dict]:
        """Islamabad High Court — ihc.gov.pk"""
        page = await context.new_page()
        results = []
        try:
            await page.goto("https://ihc.gov.pk/", timeout=TIMEOUT, wait_until="domcontentloaded")

            # Look for case search link/section
            search_link = page.locator("a:has-text('Case'), a:has-text('Search'), a:has-text('Cause List')").first
            if await search_link.count() > 0:
                await search_link.click()
                await page.wait_for_load_state("domcontentloaded", timeout=TIMEOUT)

            name_input = page.locator("input[type='text']").first
            if await name_input.count() > 0:
                await name_input.fill(full_name)
                await page.keyboard.press("Enter")
                await page.wait_for_load_state("networkidle", timeout=TIMEOUT)

                content = await page.content()
                if full_name.split()[0].lower() in content.lower():
                    results.append({
                        "source": "Islamabad High Court",
                        "note": f"Name '{full_name}' found — visit ihc.gov.pk to review case details",
                        "url": page.url,
                    })

        except PWTimeout:
            results.append({"source": "Islamabad High Court", "note": "Timed out — visit ihc.gov.pk manually"})
        except Exception as e:
            results.append({"source": "Islamabad High Court", "error": str(e)})
        finally:
            await page.close()
        return results

    async def _search_shc(self, context, full_name: str) -> list[dict]:
        """Sindh High Court — shc.gov.pk"""
        page = await context.new_page()
        results = []
        try:
            await page.goto("https://www.shc.gov.pk/", timeout=TIMEOUT, wait_until="domcontentloaded")

            # SHC has a cause list search
            cause_link = page.locator("a:has-text('Cause List'), a:has-text('Case Status'), a:has-text('Search')").first
            if await cause_link.count() > 0:
                await cause_link.click()
                await page.wait_for_load_state("domcontentloaded", timeout=TIMEOUT)

            name_input = page.locator("input[type='text'], input[name*='name'], input[name*='party']").first
            if await name_input.count() > 0:
                await name_input.fill(full_name)
                await page.keyboard.press("Enter")
                await page.wait_for_load_state("networkidle", timeout=TIMEOUT)

                content = await page.content()
                if full_name.split()[0].lower() in content.lower():
                    results.append({
                        "source": "Sindh High Court",
                        "note": f"Name '{full_name}' found — visit shc.gov.pk to review case details",
                        "url": page.url,
                    })

        except PWTimeout:
            results.append({"source": "Sindh High Court", "note": "Timed out — visit shc.gov.pk manually"})
        except Exception as e:
            results.append({"source": "Sindh High Court", "error": str(e)})
        finally:
            await page.close()
        return results

    async def _search_phc(self, context, full_name: str) -> list[dict]:
        """Peshawar High Court — peshawarhighcourt.com.pk"""
        page = await context.new_page()
        results = []
        try:
            await page.goto("https://www.peshawarhighcourt.com.pk/", timeout=TIMEOUT, wait_until="domcontentloaded")

            name_input = page.locator("input[type='text'], input[name*='name'], input[name*='party']").first
            if await name_input.count() > 0:
                await name_input.fill(full_name)
                await page.keyboard.press("Enter")
                await page.wait_for_load_state("networkidle", timeout=TIMEOUT)

                content = await page.content()
                if full_name.split()[0].lower() in content.lower():
                    results.append({
                        "source": "Peshawar High Court",
                        "note": f"Name '{full_name}' found — visit peshawarhighcourt.com.pk to review",
                        "url": page.url,
                    })

        except PWTimeout:
            results.append({"source": "Peshawar High Court", "note": "Timed out — visit peshawarhighcourt.com.pk manually"})
        except Exception as e:
            results.append({"source": "Peshawar High Court", "error": str(e)})
        finally:
            await page.close()
        return results

    async def _search_supreme_court(self, context, full_name: str) -> list[dict]:
        """Supreme Court of Pakistan — supremecourt.gov.pk"""
        page = await context.new_page()
        results = []
        try:
            await page.goto("https://www.supremecourt.gov.pk/", timeout=TIMEOUT, wait_until="domcontentloaded")

            # Try judgment search
            search_link = page.locator("a:has-text('Judgment'), a:has-text('Search'), a:has-text('Cause List')").first
            if await search_link.count() > 0:
                await search_link.click()
                await page.wait_for_load_state("domcontentloaded", timeout=TIMEOUT)

            name_input = page.locator("input[type='text'], input[name*='search'], input[name*='party']").first
            if await name_input.count() > 0:
                await name_input.fill(full_name)
                await page.keyboard.press("Enter")
                await page.wait_for_load_state("networkidle", timeout=TIMEOUT)

                # Extract results
                rows = await page.locator("table tr, .result-item, .case-row").all()
                for row in rows[:10]:
                    text = (await row.inner_text()).strip()
                    if text and len(text) > 10:
                        results.append({
                            "source": "Supreme Court of Pakistan",
                            "record": text[:300],
                            "url": page.url,
                        })

            if not results:
                # Check if name mentioned anywhere
                content = await page.content()
                if full_name.split()[0].lower() in content.lower():
                    results.append({
                        "source": "Supreme Court of Pakistan",
                        "note": f"Name '{full_name}' found on Supreme Court site",
                        "url": page.url,
                    })

        except PWTimeout:
            results.append({"source": "Supreme Court of Pakistan", "note": "Timed out — visit supremecourt.gov.pk manually"})
        except Exception as e:
            results.append({"source": "Supreme Court of Pakistan", "error": str(e)})
        finally:
            await page.close()
        return results
