-- ─────────────────────────────────────────────────────────────────────────────
-- Migration 005: Add user_id to cases for multi-user support
-- Run this after enabling Supabase Auth in your project dashboard.
-- ─────────────────────────────────────────────────────────────────────────────

-- 1. Add user_id column to cases (nullable initially for backwards compat)
alter table cases
  add column if not exists user_id uuid references auth.users(id) on delete cascade;

-- 2. Drop the open dev policies
drop policy if exists "allow_all_cases" on cases;
drop policy if exists "allow_all_subjects" on subjects;
drop policy if exists "allow_all_jobs" on investigation_jobs;
drop policy if exists "allow_all_reports" on reports;

-- 3. Add user-scoped RLS policies
--    cases: owner access only
create policy "cases_owner" on cases
  for all
  using (auth.uid() = user_id);

--    subjects: access if parent case is owned by the user
create policy "subjects_owner" on subjects
  for all
  using (
    exists (
      select 1 from cases
      where cases.id = subjects.case_id
        and cases.user_id = auth.uid()
    )
  );

--    investigation_jobs: same ownership chain via cases
create policy "jobs_owner" on investigation_jobs
  for all
  using (
    exists (
      select 1 from cases
      where cases.id = investigation_jobs.case_id
        and cases.user_id = auth.uid()
    )
  );

--    reports: same ownership chain via cases
create policy "reports_owner" on reports
  for all
  using (
    exists (
      select 1 from cases
      where cases.id = reports.case_id
        and cases.user_id = auth.uid()
    )
  );

-- 4. Allow the service-role backend to bypass RLS (already the case — no change needed).
--    The backend enforces user_id explicitly in every query.
