"""
Report generator: takes the agent's narrative output and raw tool findings,
then calls Claude once more to produce a structured report dict
matching the database schema.
"""

import json
import re
from datetime import date
from anthropic import AsyncAnthropic
from config import settings


# full_report_md and sources_consulted are placed LAST so that if the output
# is ever truncated, the structured fields above them survive intact.
REPORT_SYSTEM_PROMPT = """You are a legal report formatter. You will receive:
1. A narrative investigation summary written by an AI agent
2. Raw data findings from various search tools

Your job is to produce a structured JSON report with these exact keys:
{
  "court_records": { "federal": [], "state": [] },
  "property_records": { "owned": [], "notes": "" },
  "business_filings": { "active": [], "historical": [] },
  "social_media": { "platforms": {} },
  "employment": { "current": null, "history": [], "licenses": [] },
  "family_info": { "spouse": null, "known_associates": [] },
  "executive_summary": "2-3 sentence summary",
  "asset_summary": "Summary of findable assets",
  "risk_flags": ["flag1", "flag2"],
  "confidence_score": 0.0,
  "sources_consulted": ["source1"],
  "full_report_md": "Full markdown report — place this LAST"
}

For confidence_score: 0.0-1.0 reflecting how complete the data is.
For full_report_md: a well-formatted markdown document for attorney review.
  Keep it under 2000 words so the full JSON fits within the response limit.
Always populate sources_consulted with every data source that was checked.
Return ONLY valid JSON. No preamble, no markdown code fences."""


def _repair_truncated_json(raw: str) -> dict:
    """
    Attempt to recover a JSON object that was cut off mid-stream.
    Tries progressively more aggressive closing sequences.
    If all fail, returns a minimal fallback dict.
    """
    candidates = [
        raw,
        raw + '"',
        raw + '"}',
        raw + '"}}',
        raw + '"}}}',
    ]
    # Also try removing the last (likely incomplete) field
    last_comma = raw.rfind(",")
    if last_comma > 0:
        trimmed = raw[:last_comma]
        candidates += [
            trimmed + "}",
            trimmed + "}}",
        ]

    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue

    # Final fallback: extract whatever text we have and return a minimal report
    summary_match = re.search(r'"executive_summary"\s*:\s*"([^"]*)"', raw)
    return {
        "executive_summary": summary_match.group(1) if summary_match else "Report generation was truncated.",
        "full_report_md": raw,
        "risk_flags": [],
        "sources_consulted": [],
        "confidence_score": 0.0,
        "court_records": None,
        "property_records": None,
        "business_filings": None,
        "social_media": None,
        "employment": None,
        "family_info": None,
        "asset_summary": None,
    }


async def generate_report(
    agent_narrative: str,
    raw_findings: dict,
    subject: dict,
) -> dict:
    """
    Call Claude to synthesize the agent output into a structured report.
    Returns a dict matching the reports table columns.
    """
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    photo_note = (
        "A photograph of the subject was provided and analyzed by the investigating agent."
        if subject.get("photo_url")
        else "No photograph was provided for this subject."
    )

    prompt = f"""Subject: {subject.get('full_name')}
Investigation Date: {date.today().isoformat()}
Photo: {photo_note}

--- AGENT NARRATIVE ---
{agent_narrative}

--- RAW TOOL FINDINGS ---
{json.dumps(raw_findings, indent=2, default=str)}

Produce the structured JSON report now. When calculating confidence_score, treat the
presence of a verified subject photograph as a positive signal that raises confidence."""

    response = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=16000,
        system=REPORT_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_json = response.content[0].text.strip()

    # Strip markdown fences if Claude adds them despite instructions
    if raw_json.startswith("```"):
        raw_json = raw_json.split("```")[1]
        if raw_json.startswith("json"):
            raw_json = raw_json[4:]
        raw_json = raw_json.strip()
    if raw_json.endswith("```"):
        raw_json = raw_json[: raw_json.rfind("```")].strip()

    # Warn if the response was cut off at the token limit
    if response.stop_reason == "max_tokens":
        import logging
        logging.warning(
            "generate_report: response hit max_tokens (%d). "
            "Attempting JSON repair.", 16000
        )

    try:
        return json.loads(raw_json)
    except json.JSONDecodeError:
        return _repair_truncated_json(raw_json)
