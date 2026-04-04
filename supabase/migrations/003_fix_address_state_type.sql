-- Widen address_state from char(2) to text to support non-US provinces/regions
alter table subjects alter column address_state type text;
