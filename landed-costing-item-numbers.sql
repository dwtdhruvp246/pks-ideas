-- Run once in the existing Supabase project's SQL Editor, then reload the app.
-- Safe to rerun. Existing catalogue and saved history are preserved.
begin;
alter table public.landed_items
 add column if not exists item_number text not null default '' check (length(item_number) <= 80);
alter table public.landed_cost_list_items
 add column if not exists item_number text not null default '' check (length(item_number) <= 80);

-- Never delete or merge existing rows to make a constraint succeed.
do $$
begin
 if exists (
  select 1 from public.landed_items
  group by user_id, lower(trim(supplier)), lower(trim(name)), lower(trim(item_number)), lower(trim(colour))
  having count(*) > 1
 ) then
  raise exception 'Duplicate catalogue identities exist. No changes were applied. Resolve items with the same supplier, name, item number and colour, then rerun this migration.';
 end if;
end $$;

create unique index if not exists landed_items_identity_unique
 on public.landed_items (user_id, lower(trim(supplier)), lower(trim(name)), lower(trim(item_number)), lower(trim(colour)));
notify pgrst, 'reload schema';
commit;
