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
  website_url text check (website_url is null or char_length(website_url) <= 500),
  github_url text check (github_url is null or char_length(github_url) <= 500),
  notes text check (notes is null or char_length(notes) <= 5000),
  next_step text check (next_step is null or char_length(next_step) <= 250),
  due_date date,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

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
