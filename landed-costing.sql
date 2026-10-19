-- Pks Ideas: Landed Costing workspace (run once in Supabase SQL Editor)
-- Separate tables; does not alter existing Ideas, Notes, or Checklist tables.
create extension if not exists pgcrypto;

create table if not exists public.landed_items (
 id uuid primary key default gen_random_uuid(),
 user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
 name text not null check (length(trim(name)) between 1 and 180),
 supplier text not null default '',
 item_number text not null default '' check (length(item_number) <= 80),
 colour text not null default '',
 base_price numeric(16,4) not null default 0 check (base_price >= 0),
 local_shipping numeric(16,4) not null default 0 check (local_shipping >= 0),
 units_per_carton integer not null default 1 check (units_per_carton >= 1),
 carton_length_cm numeric(14,4) not null default 0 check (carton_length_cm >= 0),
 carton_width_cm numeric(14,4) not null default 0 check (carton_width_cm >= 0),
 carton_height_cm numeric(14,4) not null default 0 check (carton_height_cm >= 0),
 created_at timestamptz not null default now()
);

create unique index if not exists landed_items_identity_unique
 on public.landed_items (user_id, lower(trim(supplier)), lower(trim(name)), lower(trim(item_number)), lower(trim(colour)));

create table if not exists public.landed_price_tiers (
 id uuid primary key default gen_random_uuid(),
 user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
 item_id uuid not null references public.landed_items(id) on delete cascade,
 min_qty integer not null check (min_qty >= 1),
 max_qty integer check (max_qty >= min_qty),
 unit_price numeric(16,4) not null check (unit_price >= 0)
);
create index if not exists landed_tiers_item_idx on public.landed_price_tiers(item_id);

create table if not exists public.landed_settings (
 user_id uuid primary key default auth.uid() references auth.users(id) on delete cascade,
 fee_percent numeric(9,4) not null default 0 check (fee_percent between 0 and 100),
 intl_shipping_per_cbm numeric(16,4) not null default 0 check (intl_shipping_per_cbm >= 0)
);

create table if not exists public.landed_cost_lists (
 id uuid primary key default gen_random_uuid(),
 user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
 name text not null check (length(trim(name)) between 1 and 180),
 notes text not null default '',
 fee_percent numeric(9,4) not null check (fee_percent between 0 and 100),
 intl_shipping_per_cbm numeric(16,4) not null check (intl_shipping_per_cbm >= 0),
 total_cost numeric(18,4) not null check (total_cost >= 0),
 total_cbm numeric(18,8) not null check (total_cbm >= 0),
 total_cartons integer not null check (total_cartons >= 0),
 created_at timestamptz not null default now()
);

create table if not exists public.landed_cost_list_items (
 id uuid primary key default gen_random_uuid(),
 user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
 list_id uuid not null references public.landed_cost_lists(id) on delete cascade,
 source_item_id uuid, -- intentionally no FK: historical lists survive catalogue deletion
 item_name text not null,
 supplier text not null default '',
 item_number text not null default '' check (length(item_number) <= 80),
 colour text not null default '',
 quantity integer not null check (quantity >= 1),
 unit_price numeric(16,4) not null check (unit_price >= 0),
 local_shipping numeric(16,4) not null check (local_shipping >= 0),
 cost_price numeric(18,4) not null check (cost_price >= 0),
 fees numeric(18,4) not null check (fees >= 0),
 cartons integer not null check (cartons >= 1),
 units_per_carton integer not null check (units_per_carton >= 1),
 carton_length_cm numeric(14,4) not null check (carton_length_cm >= 0),
 carton_width_cm numeric(14,4) not null check (carton_width_cm >= 0),
 carton_height_cm numeric(14,4) not null check (carton_height_cm >= 0),
 cbm numeric(18,8) not null check (cbm >= 0),
 intl_shipping numeric(18,4) not null check (intl_shipping >= 0),
 total_cost numeric(18,4) not null check (total_cost >= 0)
);
create index if not exists landed_list_items_list_idx on public.landed_cost_list_items(list_id);

alter table public.landed_items enable row level security;
alter table public.landed_price_tiers enable row level security;
alter table public.landed_settings enable row level security;
alter table public.landed_cost_lists enable row level security;
alter table public.landed_cost_list_items enable row level security;

-- Explicit ownership, with child-parent match on BOTH reads and writes.
drop policy if exists landed_items_owner on public.landed_items;
create policy landed_items_owner on public.landed_items for all to authenticated
 using (user_id = (select auth.uid())) with check (user_id = (select auth.uid()));

drop policy if exists landed_settings_owner on public.landed_settings;
create policy landed_settings_owner on public.landed_settings for all to authenticated
 using (user_id = (select auth.uid())) with check (user_id = (select auth.uid()));

drop policy if exists landed_lists_owner on public.landed_cost_lists;
create policy landed_lists_owner on public.landed_cost_lists for all to authenticated
 using (user_id = (select auth.uid())) with check (user_id = (select auth.uid()));

drop policy if exists landed_tiers_owner on public.landed_price_tiers;
create policy landed_tiers_owner on public.landed_price_tiers for all to authenticated
 using (user_id = (select auth.uid()) and exists
 (select 1 from public.landed_items i where i.id = item_id and i.user_id = (select auth.uid())))
 with check (user_id = (select auth.uid()) and exists
 (select 1 from public.landed_items i where i.id = item_id and i.user_id = (select auth.uid())));

drop policy if exists landed_list_items_owner on public.landed_cost_list_items;
create policy landed_list_items_owner on public.landed_cost_list_items for all to authenticated
 using (user_id = (select auth.uid()) and exists
 (select 1 from public.landed_cost_lists l where l.id = list_id and l.user_id = (select auth.uid())))
 with check (user_id = (select auth.uid()) and exists
 (select 1 from public.landed_cost_lists l where l.id = list_id and l.user_id = (select auth.uid())));

grant select, insert, update, delete on public.landed_items, public.landed_price_tiers,
 public.landed_settings, public.landed_cost_lists, public.landed_cost_list_items to authenticated;
