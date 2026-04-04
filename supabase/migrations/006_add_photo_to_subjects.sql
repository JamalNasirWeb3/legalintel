-- Migration 006: Add photo_url to subjects for debtor photo upload
alter table subjects
  add column if not exists photo_url text;
