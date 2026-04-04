-- Add country field to subjects table
alter table subjects add column if not exists country char(2) not null default 'US';
