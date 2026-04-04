# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Legal Intelligence System** — An AI agent for attorneys to investigate judgment debtors by aggregating publicly available information into structured reports. The system searches public records including social media, court records, land ownership, employment, and business affiliations.

**Constraint**: Only lawful public records and publicly visible web data — no private or restricted data sources.

## Tech Stack

- **Frontend**: Next.js 14 (App Router, TypeScript, Tailwind CSS)
- **Backend**: Python 3.11+ with FastAPI
- **Web Scraping**: `httpx` (async HTTP); `playwright` is installed but not yet used in scrapers
- **Database**: PostgreSQL via Supabase
- **AI Agent**: Claude API (`claude-opus-4-6` for investigation, `claude-sonnet-4-6` for report synthesis)

## Development Commands

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
cp ../.env.example .env   # fill in your keys
python run.py   # preferred: sets keepalive + graceful shutdown timeouts
# OR: uvicorn main:app --reload  (but may ECONNRESET during long investigations)
```

### Frontend
```bash
cd frontend
npm install
cp ../.env.example .env.local   # fill in NEXT_PUBLIC_* keys
npm run dev
```

### Tests
```bash
cd backend
pytest tests/
pytest tests/test_scrapers.py::test_court_records_returns_structure  # single test
```

### Database
Apply all three migrations in order via Supabase dashboard SQL editor (or CLI):
```bash
supabase db push   # if using Supabase CLI
# OR paste supabase/migrations/001_initial_schema.sql, 002_add_country_to_subjects.sql,
#    and 003_fix_address_state_type.sql into the SQL editor in order
```

## Architecture

```
frontend/src/
  app/
    cases/           # Case list + new case form
    cases/[id]/      # Case detail + "Run Investigation" button
    cases/[id]/report/[reportId]/  # Report viewer
  lib/api.ts         # All fetch calls to FastAPI (typed); requests proxied via Next.js rewrite at /api/backend
  types/index.ts     # TypeScript types (mirror backend Pydantic models)

backend/
  main.py            # FastAPI app, CORS, router mounts, rate limiter
  config.py          # pydantic-settings reads .env; fails fast if keys missing
  database.py        # Supabase client singleton
  limiter.py         # slowapi rate limiter (IP-based)
  routers/           # REST endpoints (cases, subjects, agent, reports)
  agents/
    investigator.py  # Main Claude tool-use loop (run_investigation)
    tools.py         # Tool definitions (TOOL_DEFINITIONS list + dispatch_tool + get_tools_for_country)
    prompts.py       # System prompt governing agent behavior and legal constraints
  scrapers/          # One module per data source, all extend BaseScraper
    base.py          # BaseScraper ABC with _ok/_no_results/_unavailable helpers
    # US: court_records, property_records, business_filings, social_media, employment, people_search
    # Pakistan: pk_courts, pk_business, pk_news, pk_social_media
  reports/generator.py  # Final Claude call to structure raw findings into report JSON
```

### Agent flow
1. `POST /agent/run` (rate-limited to 5/min per IP) creates an `investigation_jobs` row and kicks off `_run_agent` as a FastAPI `BackgroundTask`
2. `_run_agent` calls `agents/investigator.py::run_investigation(subject)`
3. `run_investigation` selects tools via `get_tools_for_country(country)`, then runs a Claude tool-use loop (up to 20 rounds), dispatching scrapers via `dispatch_tool`. API calls retry up to 4 times with exponential backoff (10s → 20s → 40s) on 429/529 errors.
4. When Claude stops calling tools, `reports/generator.py::generate_report` makes a second Claude call to produce structured JSON
5. Report is saved to `reports` table; job status updated to `"complete"`
6. Frontend polls `GET /agent/status/{job_id}` every 3 seconds until done, then loads the report

### Country routing
The `subject.country` field (`"US"` or `"PK"`) controls which tool set the agent receives. `get_tools_for_country()` in `agents/tools.py` filters `TOOL_DEFINITIONS` by country tag. Pakistan subjects get `pk_courts`, `pk_business`, `pk_news`, `pk_social_media`; US subjects get the six US tools.

### Scraper contracts
Every scraper returns `{"status": "ok"|"no_results"|"unavailable", "source": str, "results": list}` — never raises. Use `BaseScraper._ok()`, `._no_results()`, `._unavailable()` helpers. The agent notes data gaps in the report rather than erroring.

### Report JSON schema
`generate_report()` expects `claude-sonnet-4-6` to return JSON with these top-level keys:
```
court_records, property_records, business_filings, social_media, employment, family_info,
executive_summary, asset_summary, risk_flags, full_report_md, confidence_score, sources_consulted
```
These map 1:1 to columns in the `reports` table and fields in `types/index.ts`.

### Frontend API proxy
All frontend API calls in `lib/api.ts` target `/api/backend/...`, which Next.js rewrites to `NEXT_PUBLIC_API_URL` (the FastAPI server). This avoids browser-level CORS entirely — do not add `fetch` calls that bypass this proxy.

## Environment Variables

See `.env.example`. Backend needs: `ANTHROPIC_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`.
Frontend needs: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `NEXT_PUBLIC_API_URL`.

## Adding a New Data Source

1. Create `backend/scrapers/my_source.py` extending `BaseScraper`; use `_ok`/`_no_results`/`_unavailable` helpers
2. Add a tool definition object to `TOOL_DEFINITIONS` in `agents/tools.py` with a `country` tag (`"US"` or `"PK"`)
3. Add a dispatch branch in `dispatch_tool` in `agents/tools.py`
4. The agent will automatically use the new tool on the next run for matching-country subjects
