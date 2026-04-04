-- Enable UUID generation
create extension if not exists "uuid-ossp";

-- ─────────────────────────────────────────
-- CASES: one per engagement (attorney + debtor)
-- ─────────────────────────────────────────
create table cases (
  id               uuid primary key default uuid_generate_v4(),
  created_at       timestamptz not null default now(),
  updated_at       timestamptz not null default now(),
  title            text not null,
  attorney_name    text,
  client_name      text,
  judgment_amount  numeric(12,2),
  notes            text,
  status           text not null default 'open'
    check (status in ('open','active','closed'))
);

-- ─────────────────────────────────────────
-- SUBJECTS: the judgment debtor being investigated
-- ─────────────────────────────────────────
create table subjects (
  id                uuid primary key default uuid_generate_v4(),
  case_id           uuid not null references cases(id) on delete cascade,
  created_at        timestamptz not null default now(),
  full_name         text not null,
  aliases           text[],
  date_of_birth     date,
  address_street    text,
  address_city      text,
  address_state     char(2),
  address_zip       text,
  ssn_last4         char(4),
  known_employers   text[],
  known_spouses     text[],
  known_businesses  text[]
);

-- ─────────────────────────────────────────
-- INVESTIGATION JOBS: tracks async agent runs
-- ─────────────────────────────────────────
create table investigation_jobs (
  id            uuid primary key default uuid_generate_v4(),
  case_id       uuid not null references cases(id) on delete cascade,
  subject_id    uuid not null references subjects(id) on delete cascade,
  created_at    timestamptz not null default now(),
  started_at    timestamptz,
  completed_at  timestamptz,
  status        text not null default 'pending'
    check (status in ('pending','running','complete','failed')),
  error_message text,
  raw_findings  jsonb
);

-- ─────────────────────────────────────────
-- REPORTS: structured output of each investigation
-- ─────────────────────────────────────────
create table reports (
  id                uuid primary key default uuid_generate_v4(),
  case_id           uuid not null references cases(id) on delete cascade,
  job_id            uuid not null references investigation_jobs(id) on delete cascade,
  created_at        timestamptz not null default now(),
  court_records     jsonb,
  property_records  jsonb,
  business_filings  jsonb,
  social_media      jsonb,
  employment        jsonb,
  family_info       jsonb,
  executive_summary text,
  asset_summary     text,
  risk_flags        text[],
  full_report_md    text,
  confidence_score  numeric(3,2),
  sources_consulted text[]
);

-- ─────────────────────────────────────────
-- INDEXES
-- ─────────────────────────────────────────
create index idx_subjects_case_id on subjects(case_id);
create index idx_jobs_case_id on investigation_jobs(case_id);
create index idx_jobs_status on investigation_jobs(status);
create index idx_reports_case_id on reports(case_id);
create index idx_reports_job_id on reports(job_id);

-- ─────────────────────────────────────────
-- UPDATED_AT trigger
-- ─────────────────────────────────────────
create or replace function update_updated_at_column()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger update_cases_updated_at
  before update on cases
  for each row execute procedure update_updated_at_column();

-- ─────────────────────────────────────────
-- ROW LEVEL SECURITY (open for dev — lock down before production)
-- ─────────────────────────────────────────
alter table cases enable row level security;
alter table subjects enable row level security;
alter table investigation_jobs enable row level security;
alter table reports enable row level security;

create policy "allow_all_cases" on cases for all using (true);
create policy "allow_all_subjects" on subjects for all using (true);
create policy "allow_all_jobs" on investigation_jobs for all using (true);
create policy "allow_all_reports" on reports for all using (true);
