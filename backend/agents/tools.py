"""
Tool definitions for the investigator agent.
Each function is decorated with the schema needed by the Anthropic tool_use API.
The functions themselves call the underlying scrapers.
"""

import json
from scrapers.court_records import CourtRecordsScraper
from scrapers.property_records import PropertyRecordsScraper
from scrapers.business_filings import BusinessFilingsScraper
from scrapers.social_media import SocialMediaScraper
from scrapers.employment import EmploymentScraper
from scrapers.people_search import PeopleSearchScraper
from scrapers.pk_courts import PakistanCourtsScraper
from scrapers.pk_business import PakistanBusinessScraper
from scrapers.pk_news import PakistanNewsScraper
from scrapers.pk_social_media import PakistanSocialMediaScraper


US_TOOL_NAMES = {
    "search_court_records",
    "search_property_records",
    "search_business_filings",
    "search_social_media",
    "search_employment",
    "search_people_records",
}

PK_TOOL_NAMES = {
    "search_pakistan_courts",
    "search_pakistan_business",
    "search_pakistan_news",
    "search_pakistan_social_media",
}


def get_tools_for_country(country: str) -> list[dict]:
    """Return tools relevant for the given country code.
    'BOTH' returns all US + PK tools for cross-jurisdiction subjects.
    """
    country = country.upper()
    if country == "PK":
        allowed = PK_TOOL_NAMES
    elif country == "BOTH":
        allowed = US_TOOL_NAMES | PK_TOOL_NAMES
    else:
        allowed = US_TOOL_NAMES
    return [t for t in TOOL_DEFINITIONS if t["name"] in allowed]


# Tool schema definitions (passed to the Anthropic API as tools=[...])
TOOL_DEFINITIONS = [
    # ── US tools ─────────────────────────────────────────────────────────────
    {
        "name": "search_court_records",
        "description": (
            "Search US federal and state court records (CourtListener/PACER) for lawsuits "
            "filed by or against this person. Use for US-based subjects only."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "full_name": {"type": "string", "description": "The person's full legal name"},
                "state": {"type": "string", "description": "Two-letter US state code, e.g. CO"},
                "date_of_birth": {"type": "string", "description": "Optional. Format YYYY-MM-DD"},
            },
            "required": ["full_name", "state"],
        },
    },
    {
        "name": "search_property_records",
        "description": (
            "Search US county property/assessor records for real estate owned by this person. "
            "Use for US-based subjects only."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "full_name": {"type": "string", "description": "The person's full legal name"},
                "state": {"type": "string", "description": "Two-letter US state code"},
                "city": {"type": "string", "description": "Optional. City to narrow search"},
            },
            "required": ["full_name", "state"],
        },
    },
    {
        "name": "search_business_filings",
        "description": (
            "Search US state Secretary of State filings and OpenCorporates for businesses "
            "owned or operated by this person. Use for US-based subjects."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "full_name": {"type": "string", "description": "The person's full legal name"},
                "state": {"type": "string", "description": "Two-letter US state code"},
            },
            "required": ["full_name", "state"],
        },
    },
    {
        "name": "search_social_media",
        "description": (
            "Search public social media profiles (LinkedIn, X/Twitter, Facebook) for a US-based subject."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "full_name": {"type": "string", "description": "The person's full legal name"},
                "city": {"type": "string", "description": "Optional. Known city"},
                "employer": {"type": "string", "description": "Optional. Known employer"},
            },
            "required": ["full_name"],
        },
    },
    {
        "name": "search_employment",
        "description": (
            "Search US employment info from public sources including LinkedIn and professional "
            "license databases (NPPES for healthcare providers)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "full_name": {"type": "string", "description": "The person's full legal name"},
                "state": {"type": "string", "description": "Two-letter US state code"},
                "occupation": {"type": "string", "description": "Optional. Known occupation"},
            },
            "required": ["full_name", "state"],
        },
    },
    {
        "name": "search_people_records",
        "description": (
            "Search US public people-finder records for addresses, relatives, and spouse info."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "full_name": {"type": "string", "description": "The person's full legal name"},
                "state": {"type": "string", "description": "Two-letter US state code"},
                "date_of_birth": {"type": "string", "description": "Optional. Format YYYY-MM-DD"},
            },
            "required": ["full_name", "state"],
        },
    },

    # ── Pakistan tools ───────────────────────────────────────────────────────
    {
        "name": "search_pakistan_courts",
        "description": (
            "Search Pakistani court records across Supreme Court, Lahore High Court, "
            "Islamabad High Court, Sindh High Court, and Peshawar High Court. "
            "Use for Pakistan-based subjects. Returns case links and mentions found on official court sites."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "full_name": {"type": "string", "description": "The person's full legal name"},
                "province": {
                    "type": "string",
                    "description": "Optional. Province to narrow search: punjab, sindh, kpk, islamabad, balochistan"
                },
            },
            "required": ["full_name"],
        },
    },
    {
        "name": "search_pakistan_business",
        "description": (
            "Search Pakistani business registrations via SECP (Securities and Exchange Commission "
            "of Pakistan), OpenCorporates Pakistan jurisdiction, and FBR (Federal Board of Revenue) "
            "taxpayer records. Returns companies owned or officered by this person."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "full_name": {"type": "string", "description": "The person's full legal name"},
                "company_name": {"type": "string", "description": "Optional. Known company name to search directly"},
            },
            "required": ["full_name"],
        },
    },
    {
        "name": "search_pakistan_news",
        "description": (
            "Search major Pakistani news outlets (Dawn, Geo, The News, Express Tribune, ARY News, "
            "Jang, Business Recorder) for mentions of this person. "
            "Useful for finding fraud allegations, court appearances, business dealings, and arrests."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "full_name": {"type": "string", "description": "The person's full legal name"},
                "keywords": {
                    "type": "string",
                    "description": "Optional. Additional search terms e.g. 'fraud court arrest property'"
                },
            },
            "required": ["full_name"],
        },
    },
    {
        "name": "search_pakistan_social_media",
        "description": (
            "Search public social media profiles on LinkedIn, X/Twitter, Facebook, Instagram, "
            "TikTok, and YouTube for a Pakistan-based subject. "
            "Returns profile URLs and platform details for manual review."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "full_name": {"type": "string", "description": "The person's full legal name"},
                "city": {"type": "string", "description": "Optional. City in Pakistan e.g. Karachi, Lahore"},
                "employer": {"type": "string", "description": "Optional. Known employer or business"},
            },
            "required": ["full_name"],
        },
    },
]


async def dispatch_tool(tool_name: str, tool_input: dict) -> str:
    """Route a tool call from the agent to the appropriate scraper."""
    try:
        # US tools
        if tool_name == "search_court_records":
            result = await CourtRecordsScraper().scrape(tool_input)
        elif tool_name == "search_property_records":
            result = await PropertyRecordsScraper().scrape(tool_input)
        elif tool_name == "search_business_filings":
            result = await BusinessFilingsScraper().scrape(tool_input)
        elif tool_name == "search_social_media":
            result = await SocialMediaScraper().scrape(tool_input)
        elif tool_name == "search_employment":
            result = await EmploymentScraper().scrape(tool_input)
        elif tool_name == "search_people_records":
            result = await PeopleSearchScraper().scrape(tool_input)
        # Pakistan tools
        elif tool_name == "search_pakistan_courts":
            result = await PakistanCourtsScraper().scrape(tool_input)
        elif tool_name == "search_pakistan_business":
            result = await PakistanBusinessScraper().scrape(tool_input)
        elif tool_name == "search_pakistan_news":
            result = await PakistanNewsScraper().scrape(tool_input)
        elif tool_name == "search_pakistan_social_media":
            result = await PakistanSocialMediaScraper().scrape(tool_input)
        else:
            result = {"error": f"Unknown tool: {tool_name}"}

        return json.dumps(result)

    except Exception as e:
        return json.dumps({"error": str(e), "tool": tool_name})
