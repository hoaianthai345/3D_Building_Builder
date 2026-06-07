create table if not exists public.tour_projects (
  id text primary key,
  payload jsonb not null,
  updated_at timestamptz not null default now()
);

create index if not exists tour_projects_updated_at_idx
  on public.tour_projects (updated_at desc);

alter table public.tour_projects enable row level security;

-- Backend uses SUPABASE_SERVICE_ROLE_KEY, which bypasses RLS.
-- Keep browser clients away from this table unless you later add auth-aware policies.
