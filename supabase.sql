-- ============================================================
-- IDEAVAULT: SUPABASE DATABASE SETUP
-- Run this entire file in Supabase Dashboard > SQL Editor.
-- ============================================================

create extension if not exists pgcrypto;

create table if not exists public.ideas (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  title text not null check (char_length(title) between 1 and 120),
  description text check (description is null or char_length(description) <= 2000),
  category text not null default 'Uncategorized' check (char_length(category) <= 50),
  status text not null default 'Planning' check (status in ('Planning', 'Building', 'Launched', 'Paused')),
  priority text not null default 'Medium' check (priority in ('High', 'Medium', 'Low')),
  target_user text check (target_user is null or char_length(target_user) <= 100),
  tech_stack text check (tech_stack is null or char_length(tech_stack) <= 300),
  supabase_account text check (supabase_account is null or char_length(supabase_account) <= 500),
  website_url text check (website_url is null or char_length(website_url) <= 500),
  github_url text check (github_url is null or char_length(github_url) <= 500),
  notes text check (notes is null or char_length(notes) <= 5000),
  next_step text check (next_step is null or char_length(next_step) <= 250),
  due_date date,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Adds the field safely when upgrading an existing database.
alter table public.ideas
  add column if not exists supabase_account text;

alter table public.ideas
  drop constraint if exists ideas_supabase_account_check;

alter table public.ideas
  add constraint ideas_supabase_account_check
  check (supabase_account is null or char_length(supabase_account) <= 500);

create index if not exists ideas_user_id_idx on public.ideas(user_id);
create index if not exists ideas_status_idx on public.ideas(status);
create index if not exists ideas_created_at_idx on public.ideas(created_at desc);

create or replace function public.set_updated_at()
returns trigger
language plpgsql
security invoker
set search_path = public
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists ideas_set_updated_at on public.ideas;
create trigger ideas_set_updated_at
before update on public.ideas
for each row execute function public.set_updated_at();

alter table public.ideas enable row level security;

-- Remove old policies if the script is run more than once.
drop policy if exists "Owner can view own ideas" on public.ideas;
drop policy if exists "Owner can add own ideas" on public.ideas;
drop policy if exists "Owner can update own ideas" on public.ideas;
drop policy if exists "Owner can delete own ideas" on public.ideas;

-- Two checks are deliberately used:
-- 1. The row must belong to the logged-in Supabase user UUID.
-- 2. The authenticated email must be the one allowed for this private site.
create policy "Owner can view own ideas"
on public.ideas
for select
to authenticated
using (
  (select auth.uid()) = user_id
  and lower(coalesce((select auth.jwt() ->> 'email'), '')) = 'dhruvp246@gmail.com'
);

create policy "Owner can add own ideas"
on public.ideas
for insert
to authenticated
with check (
  (select auth.uid()) = user_id
  and lower(coalesce((select auth.jwt() ->> 'email'), '')) = 'dhruvp246@gmail.com'
);

create policy "Owner can update own ideas"
on public.ideas
for update
to authenticated
using (
  (select auth.uid()) = user_id
  and lower(coalesce((select auth.jwt() ->> 'email'), '')) = 'dhruvp246@gmail.com'
)
with check (
  (select auth.uid()) = user_id
  and lower(coalesce((select auth.jwt() ->> 'email'), '')) = 'dhruvp246@gmail.com'
);

create policy "Owner can delete own ideas"
on public.ideas
for delete
to authenticated
using (
  (select auth.uid()) = user_id
  and lower(coalesce((select auth.jwt() ->> 'email'), '')) = 'dhruvp246@gmail.com'
);

-- Explicit table grants. RLS still decides which rows are accessible.
grant usage on schema public to authenticated;
grant select, insert, update, delete on table public.ideas to authenticated;
revoke all on table public.ideas from anon;



-- ============================================================
-- COSTING ITEMS
-- Each idea can have multiple monthly or yearly costs.
-- ============================================================
create table if not exists public.idea_costs (
  id uuid primary key default gen_random_uuid(),
  idea_id uuid not null references public.ideas(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  title text not null check (char_length(title) between 1 and 120),
  cost_amount numeric(12,2) not null check (cost_amount >= 0),
  billing_period text not null check (billing_period in ('Monthly', 'Yearly')),
  notes text check (notes is null or char_length(notes) <= 1000),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idea_costs_idea_id_idx on public.idea_costs(idea_id);
create index if not exists idea_costs_user_id_idx on public.idea_costs(user_id);

drop trigger if exists idea_costs_set_updated_at on public.idea_costs;
create trigger idea_costs_set_updated_at
before update on public.idea_costs
for each row execute function public.set_updated_at();

alter table public.idea_costs enable row level security;

drop policy if exists "Owner can view own idea costs" on public.idea_costs;
drop policy if exists "Owner can add own idea costs" on public.idea_costs;
drop policy if exists "Owner can update own idea costs" on public.idea_costs;
drop policy if exists "Owner can delete own idea costs" on public.idea_costs;

create policy "Owner can view own idea costs"
on public.idea_costs for select to authenticated
using (
  (select auth.uid()) = user_id
  and lower(coalesce((select auth.jwt() ->> 'email'), '')) = 'dhruvp246@gmail.com'
  and exists (select 1 from public.ideas i where i.id = idea_id and i.user_id = (select auth.uid()))
);

create policy "Owner can add own idea costs"
on public.idea_costs for insert to authenticated
with check (
  (select auth.uid()) = user_id
  and lower(coalesce((select auth.jwt() ->> 'email'), '')) = 'dhruvp246@gmail.com'
  and exists (select 1 from public.ideas i where i.id = idea_id and i.user_id = (select auth.uid()))
);

create policy "Owner can update own idea costs"
on public.idea_costs for update to authenticated
using ((select auth.uid()) = user_id)
with check (
  (select auth.uid()) = user_id
  and lower(coalesce((select auth.jwt() ->> 'email'), '')) = 'dhruvp246@gmail.com'
);

create policy "Owner can delete own idea costs"
on public.idea_costs for delete to authenticated
using (
  (select auth.uid()) = user_id
  and lower(coalesce((select auth.jwt() ->> 'email'), '')) = 'dhruvp246@gmail.com'
);

grant select, insert, update, delete on table public.idea_costs to authenticated;
revoke all on table public.idea_costs from anon;


-- Enable Realtime for costing too, so cost changes sync across devices.
do $$
begin
  if not exists (
    select 1 from pg_publication_tables
    where pubname = 'supabase_realtime'
      and schemaname = 'public'
      and tablename = 'idea_costs'
  ) then
    alter publication supabase_realtime add table public.idea_costs;
  end if;
end $$;

-- Enable Supabase Realtime for cross-device updates.
-- The block is safe to run repeatedly.
do $$
begin
  if not exists (
    select 1
    from pg_publication_tables
    where pubname = 'supabase_realtime'
      and schemaname = 'public'
      and tablename = 'ideas'
  ) then
    alter publication supabase_realtime add table public.ideas;
  end if;
end $$;


-- ============================================================
-- DASHBOARD NOTES
-- One synced scratchpad / to-do note per authenticated user.
-- ============================================================
create table if not exists public.dashboard_notes (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null unique references auth.users(id) on delete cascade,
  content text not null default '' check (char_length(content) <= 10000),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists dashboard_notes_user_id_idx on public.dashboard_notes(user_id);

drop trigger if exists dashboard_notes_set_updated_at on public.dashboard_notes;
create trigger dashboard_notes_set_updated_at
before update on public.dashboard_notes
for each row execute function public.set_updated_at();

alter table public.dashboard_notes enable row level security;

drop policy if exists "Owner can view own dashboard note" on public.dashboard_notes;
drop policy if exists "Owner can add own dashboard note" on public.dashboard_notes;
drop policy if exists "Owner can update own dashboard note" on public.dashboard_notes;
drop policy if exists "Owner can delete own dashboard note" on public.dashboard_notes;

create policy "Owner can view own dashboard note"
on public.dashboard_notes for select to authenticated
using (
  (select auth.uid()) = user_id
  and lower(coalesce((select auth.jwt() ->> 'email'), '')) = 'dhruvp246@gmail.com'
);

create policy "Owner can add own dashboard note"
on public.dashboard_notes for insert to authenticated
with check (
  (select auth.uid()) = user_id
  and lower(coalesce((select auth.jwt() ->> 'email'), '')) = 'dhruvp246@gmail.com'
);

create policy "Owner can update own dashboard note"
on public.dashboard_notes for update to authenticated
using (
  (select auth.uid()) = user_id
  and lower(coalesce((select auth.jwt() ->> 'email'), '')) = 'dhruvp246@gmail.com'
)
with check (
  (select auth.uid()) = user_id
  and lower(coalesce((select auth.jwt() ->> 'email'), '')) = 'dhruvp246@gmail.com'
);

create policy "Owner can delete own dashboard note"
on public.dashboard_notes for delete to authenticated
using (
  (select auth.uid()) = user_id
  and lower(coalesce((select auth.jwt() ->> 'email'), '')) = 'dhruvp246@gmail.com'
);

grant select, insert, update, delete on table public.dashboard_notes to authenticated;
revoke all on table public.dashboard_notes from anon;

-- Enable Realtime for the dashboard note so edits saved on one device
-- can appear on another open device without reloading the page.
do $$
begin
  if not exists (
    select 1
    from pg_publication_tables
    where pubname = 'supabase_realtime'
      and schemaname = 'public'
      and tablename = 'dashboard_notes'
  ) then
    alter publication supabase_realtime add table public.dashboard_notes;
  end if;
end $$;


-- ============================================================
-- MY NOTES
-- Reusable knowledge/lessons saved independently of dashboard notes.
-- ============================================================
create table if not exists public.personal_notes (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  title text not null check (char_length(title) between 1 and 160),
  project_title text check (project_title is null or char_length(project_title) <= 160),
  content text not null check (char_length(content) between 1 and 20000),
  links text check (links is null or char_length(links) <= 2000),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists personal_notes_user_id_idx on public.personal_notes(user_id);
create index if not exists personal_notes_updated_at_idx on public.personal_notes(updated_at desc);

drop trigger if exists personal_notes_set_updated_at on public.personal_notes;
create trigger personal_notes_set_updated_at
before update on public.personal_notes
for each row execute function public.set_updated_at();

alter table public.personal_notes enable row level security;

drop policy if exists "Owner can view own personal notes" on public.personal_notes;
drop policy if exists "Owner can add own personal notes" on public.personal_notes;
drop policy if exists "Owner can update own personal notes" on public.personal_notes;
drop policy if exists "Owner can delete own personal notes" on public.personal_notes;

create policy "Owner can view own personal notes"
on public.personal_notes for select to authenticated
using (
  (select auth.uid()) = user_id
  and lower(coalesce((select auth.jwt() ->> 'email'), '')) = 'dhruvp246@gmail.com'
);

create policy "Owner can add own personal notes"
on public.personal_notes for insert to authenticated
with check (
  (select auth.uid()) = user_id
  and lower(coalesce((select auth.jwt() ->> 'email'), '')) = 'dhruvp246@gmail.com'
);

create policy "Owner can update own personal notes"
on public.personal_notes for update to authenticated
using (
  (select auth.uid()) = user_id
  and lower(coalesce((select auth.jwt() ->> 'email'), '')) = 'dhruvp246@gmail.com'
)
with check (
  (select auth.uid()) = user_id
  and lower(coalesce((select auth.jwt() ->> 'email'), '')) = 'dhruvp246@gmail.com'
);

create policy "Owner can delete own personal notes"
on public.personal_notes for delete to authenticated
using (
  (select auth.uid()) = user_id
  and lower(coalesce((select auth.jwt() ->> 'email'), '')) = 'dhruvp246@gmail.com'
);

grant select, insert, update, delete on table public.personal_notes to authenticated;
revoke all on table public.personal_notes from anon;

do $$
begin
  if not exists (
    select 1 from pg_publication_tables
    where pubname = 'supabase_realtime'
      and schemaname = 'public'
      and tablename = 'personal_notes'
  ) then
    alter publication supabase_realtime add table public.personal_notes;
  end if;
end $$;


-- ============================================================
-- IDEA TEST ACCOUNTS
-- Development/testing usernames and passwords attached to an idea.
-- IMPORTANT: values are stored as application data. Use only test
-- credentials, never production or high-value secrets.
-- ============================================================
create table if not exists public.idea_test_accounts (
  id uuid primary key default gen_random_uuid(),
  idea_id uuid not null references public.ideas(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  username text not null check (char_length(username) between 1 and 250),
  password text not null check (char_length(password) between 1 and 500),
  notes text check (notes is null or char_length(notes) <= 1000),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idea_test_accounts_idea_id_idx on public.idea_test_accounts(idea_id);
create index if not exists idea_test_accounts_user_id_idx on public.idea_test_accounts(user_id);

drop trigger if exists idea_test_accounts_set_updated_at on public.idea_test_accounts;
create trigger idea_test_accounts_set_updated_at
before update on public.idea_test_accounts
for each row execute function public.set_updated_at();

alter table public.idea_test_accounts enable row level security;

drop policy if exists "Owner can view own idea test accounts" on public.idea_test_accounts;
drop policy if exists "Owner can add own idea test accounts" on public.idea_test_accounts;
drop policy if exists "Owner can update own idea test accounts" on public.idea_test_accounts;
drop policy if exists "Owner can delete own idea test accounts" on public.idea_test_accounts;

create policy "Owner can view own idea test accounts"
on public.idea_test_accounts for select to authenticated
using (
  (select auth.uid()) = user_id
  and lower(coalesce((select auth.jwt() ->> 'email'), '')) = 'dhruvp246@gmail.com'
  and exists (select 1 from public.ideas i where i.id = idea_id and i.user_id = (select auth.uid()))
);

create policy "Owner can add own idea test accounts"
on public.idea_test_accounts for insert to authenticated
with check (
  (select auth.uid()) = user_id
  and lower(coalesce((select auth.jwt() ->> 'email'), '')) = 'dhruvp246@gmail.com'
  and exists (select 1 from public.ideas i where i.id = idea_id and i.user_id = (select auth.uid()))
);

create policy "Owner can update own idea test accounts"
on public.idea_test_accounts for update to authenticated
using (
  (select auth.uid()) = user_id
  and lower(coalesce((select auth.jwt() ->> 'email'), '')) = 'dhruvp246@gmail.com'
)
with check (
  (select auth.uid()) = user_id
  and lower(coalesce((select auth.jwt() ->> 'email'), '')) = 'dhruvp246@gmail.com'
  and exists (select 1 from public.ideas i where i.id = idea_id and i.user_id = (select auth.uid()))
);

create policy "Owner can delete own idea test accounts"
on public.idea_test_accounts for delete to authenticated
using (
  (select auth.uid()) = user_id
  and lower(coalesce((select auth.jwt() ->> 'email'), '')) = 'dhruvp246@gmail.com'
);

grant select, insert, update, delete on table public.idea_test_accounts to authenticated;
revoke all on table public.idea_test_accounts from anon;

do $$
begin
  if not exists (
    select 1 from pg_publication_tables
    where pubname = 'supabase_realtime'
      and schemaname = 'public'
      and tablename = 'idea_test_accounts'
  ) then
    alter publication supabase_realtime add table public.idea_test_accounts;
  end if;
end $$;
