-- Extend country column to support multi-jurisdiction value 'BOTH'
alter table subjects alter column country type varchar(10);
