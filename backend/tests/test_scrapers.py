"""Basic smoke tests for scrapers — verify they return correct structure."""

import pytest
from scrapers.court_records import CourtRecordsScraper
from scrapers.business_filings import BusinessFilingsScraper


@pytest.mark.asyncio
async def test_court_records_returns_structure():
    scraper = CourtRecordsScraper()
    result = await scraper.scrape({"full_name": "John Smith", "state": "CO"})
    assert "status" in result
    assert "source" in result
    assert "results" in result
    assert isinstance(result["results"], list)


@pytest.mark.asyncio
async def test_business_filings_returns_structure():
    scraper = BusinessFilingsScraper()
    result = await scraper.scrape({"full_name": "John Smith", "state": "CO"})
    assert "status" in result
    assert "source" in result
    assert "results" in result
    assert isinstance(result["results"], list)


@pytest.mark.asyncio
async def test_scraper_handles_missing_name():
    scraper = CourtRecordsScraper()
    result = await scraper.scrape({"state": "CO"})
    assert result["status"] == "unavailable"
