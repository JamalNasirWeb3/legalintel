"""
Main investigation agent. Orchestrates the Claude tool-use loop,
dispatches scraper tools, then synthesizes a structured report.
"""

import asyncio
import json
import anthropic
from anthropic import AsyncAnthropic
from config import settings
from agents.prompts import INVESTIGATOR_SYSTEM_PROMPT
from agents.tools import get_tools_for_country, dispatch_tool
from reports.generator import generate_report


def _build_investigation_prompt(subject: dict) -> str:
    parts = ["Investigate the following judgment debtor:\n"]
    parts.append(f"Full name: {subject['full_name']}")

    country = subject.get("country", "US").upper()
    parts.append(f"Country: {country}")

    if subject.get("aliases"):
        parts.append(f"Known aliases: {', '.join(subject['aliases'])}")
    if subject.get("date_of_birth"):
        parts.append(f"Date of birth: {subject['date_of_birth']}")
    if subject.get("address_city") or subject.get("address_state"):
        loc = " ".join(filter(None, [subject.get("address_city"), subject.get("address_state")]))
        parts.append(f"Last known location: {loc}")
    if subject.get("address_street"):
        parts.append(f"Last known address: {subject['address_street']}, {subject.get('address_zip', '')}")
    if subject.get("known_employers"):
        parts.append(f"Known employers: {', '.join(subject['known_employers'])}")
    if subject.get("known_businesses"):
        parts.append(f"Known businesses: {', '.join(subject['known_businesses'])}")
    if subject.get("known_spouses"):
        parts.append(f"Known spouses/partners: {', '.join(subject['known_spouses'])}")

    if country == "PK":
        province = subject.get("address_state", "")
        parts.append(
            f"\nThis is a PAKISTAN-based subject. Use Pakistan-specific tools: "
            f"search_pakistan_courts (province: '{province or 'all'}'), "
            f"search_pakistan_business, search_pakistan_news (also with keywords 'fraud court property'), "
            f"and search_pakistan_social_media. "
            f"If you find company names or associates, search those in news too. "
            f"After gathering all data, produce a comprehensive report per the output format."
        )
    elif country == "BOTH":
        state = subject.get("address_state", "")
        province = state  # may be a Pakistani province or US state
        parts.append(
            f"\nThis subject has cross-jurisdiction presence (Pakistan + United States). "
            f"Run ALL available tools — both Pakistani and US — in this order:\n"
            f"1. search_pakistan_courts, search_pakistan_business, search_pakistan_news, search_pakistan_social_media\n"
            f"2. search_court_records, search_business_filings, search_property_records, search_people_records, search_employment, search_social_media\n"
            f"For US tools, use any known US state; for Pakistani tools use province '{province or 'all'}'. "
            f"If you find company names or associates during Pakistani searches, search those in US tools too and vice versa. "
            f"After gathering all data, produce a comprehensive report covering both jurisdictions."
        )
    else:
        state = subject.get("address_state", "")
        parts.append(
            f"\nUse all available tools to investigate this person thoroughly. "
            f"Start with court records and business filings for {state or 'their known state'}, "
            f"then property records, people records, employment, and social media. "
            f"If you discover additional names (maiden name, DBA), search those too. "
            f"After gathering all data, produce a comprehensive report per the output format."
        )
    return "\n".join(parts)


async def _call_with_retry(client, tools, messages, max_retries: int = 6):
    """Call Claude API with exponential backoff on overload (529) or rate-limit (429)."""
    delay = 15  # seconds; doubles each retry: 15 → 30 → 60 → 120 → 240
    for attempt in range(max_retries):
        try:
            return await client.messages.create(
                model="claude-opus-4-6",
                max_tokens=16000,
                system=INVESTIGATOR_SYSTEM_PROMPT,
                tools=tools,
                messages=messages,
            )
        except anthropic.APIStatusError as e:
            if e.status_code in (429, 529) and attempt < max_retries - 1:
                await asyncio.sleep(delay)
                delay *= 2
            else:
                raise
    raise RuntimeError("Claude API repeatedly overloaded — try again later")


async def _fetch_image_as_base64(url: str) -> dict | None:
    """Download an image from a URL and return a Claude base64 image block.

    Returns None if the download fails so the investigation can continue
    without the photo rather than crashing entirely.
    """
    import base64
    import httpx

    # Strip cache-busting query params for the actual HTTP request
    clean_url = url.split("?")[0]

    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(clean_url)
        if resp.status_code != 200:
            return None
        content_type = resp.headers.get("content-type", "image/jpeg").split(";")[0].strip()
        # Map to a type Claude accepts
        media_type_map = {
            "image/jpeg": "image/jpeg",
            "image/jpg": "image/jpeg",
            "image/png": "image/png",
            "image/gif": "image/gif",
            "image/webp": "image/webp",
        }
        media_type = media_type_map.get(content_type, "image/jpeg")
        data = base64.standard_b64encode(resp.content).decode("utf-8")
        return {
            "type": "image",
            "source": {"type": "base64", "media_type": media_type, "data": data},
        }
    except Exception as exc:
        import logging
        logging.warning("Could not fetch subject photo (%s): %s", clean_url, exc)
        return None


async def run_investigation(subject: dict) -> tuple[dict, dict]:
    """
    Run the full investigation agent loop for a subject.

    Returns:
        (report_data, raw_findings) where report_data matches the reports table schema
        and raw_findings is the full tool output log for debugging.
    """
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    investigation_prompt = _build_investigation_prompt(subject)

    if subject.get("photo_url"):
        image_block = await _fetch_image_as_base64(subject["photo_url"])
        if image_block:
            initial_content = [
                {"type": "text", "text": investigation_prompt},
                image_block,
                {
                    "type": "text",
                    "text": (
                        "The image above is a photograph of the subject. Analyze it carefully for "
                        "contextual clues that may assist the investigation: visible clothing or "
                        "uniform suggesting employer or profession, background details such as an "
                        "office, vehicle, or geographic landmarks, any visible name tags, company "
                        "logos, or signage, and lifestyle indicators. Reference these visual "
                        "observations in your report and use them to guide your tool searches "
                        "(e.g. if a company logo is visible, search that company name)."
                    ),
                },
            ]
        else:
            initial_content = investigation_prompt

    else:
        initial_content = investigation_prompt

    messages = [{"role": "user", "content": initial_content}]

    country = subject.get("country", "US").upper()
    tools = get_tools_for_country(country)

    raw_findings: dict[str, list] = {}
    max_iterations = 20  # safety cap on tool-use rounds

    for _ in range(max_iterations):
        response = await _call_with_retry(client, tools, messages)

        # Collect all tool use blocks from this response
        tool_use_blocks = [b for b in response.content if b.type == "tool_use"]

        if not tool_use_blocks:
            # No more tool calls — agent is done
            break

        # Append the assistant message with all content blocks
        messages.append({"role": "assistant", "content": response.content})

        # Execute all tool calls in parallel and build the tool_result message
        dispatched = await asyncio.gather(
            *[dispatch_tool(block.name, block.input) for block in tool_use_blocks]
        )

        tool_results = []
        for block, result_text in zip(tool_use_blocks, dispatched):
            raw_findings.setdefault(block.name, []).append({
                "input": block.input,
                "output": json.loads(result_text),
            })
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result_text,
            })

        messages.append({"role": "user", "content": tool_results})

    # The final assistant message is the agent's narrative output
    final_text = ""
    for block in response.content:
        if hasattr(block, "text"):
            final_text += block.text

    # Synthesize into structured report
    report_data = await generate_report(final_text, raw_findings, subject)

    return report_data, raw_findings
