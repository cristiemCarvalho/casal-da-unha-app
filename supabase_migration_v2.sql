-- Migração incremental para instalações que já executaram o schema inicial.
-- Execute no SQL Editor do Supabase e aguarde a conclusão sem erros.

create table if not exists public.appointments (
    id uuid primary key default gen_random_uuid(),
    studio_id uuid not null references public.studios(id) on delete cascade,
    client_id uuid not null references public.clients(id) on delete restrict,
    service_id uuid not null references public.services(id) on delete restrict,
    appointment_date date not null,
    appointment_time time not null,
    value numeric(10,2) not null default 0,
    payment_method text not null,
    status text not null default 'Agendado',
    created_at timestamptz not null default now()
);

create table if not exists public.cash_entries (
    id uuid primary key default gen_random_uuid(),
    studio_id uuid not null references public.studios(id) on delete cascade,
    appointment_id uuid unique references public.appointments(id) on delete set null,
    client_id uuid references public.clients(id) on delete set null,
    service_name text not null,
    entry_date date not null,
    value numeric(10,2) not null default 0,
    payment_method text not null,
    created_at timestamptz not null default now()
);

create table if not exists public.anamneses (
    id uuid primary key default gen_random_uuid(),
    studio_id uuid not null references public.studios(id) on delete cascade,
    client_id uuid not null unique references public.clients(id) on delete cascade,
    nail_types text[] not null default '{}',
    observations text,
    allergies text,
    health_conditions text[] not null default '{}',
    health_details text,
    signature text not null,
    accepted boolean not null default false,
    accepted_at timestamptz not null default now(),
    created_at timestamptz not null default now()
);

create table if not exists public.evolution_photos (
    id uuid primary key default gen_random_uuid(),
    studio_id uuid not null references public.studios(id) on delete cascade,
    client_id uuid not null references public.clients(id) on delete cascade,
    stage text not null check (stage in ('Antes', 'Estrutura Pronta', 'Resultado Final')),
    storage_path text not null,
    file_name text not null,
    created_at timestamptz not null default now()
);

alter table public.appointments enable row level security;
alter table public.cash_entries enable row level security;
alter table public.anamneses enable row level security;
alter table public.evolution_photos enable row level security;

drop policy if exists "owner manages own appointments" on public.appointments;
create policy "owner manages own appointments" on public.appointments for all
using (studio_id = public.current_studio_id())
with check (studio_id = public.current_studio_id());

drop policy if exists "owner manages own cash" on public.cash_entries;
create policy "owner manages own cash" on public.cash_entries for all
using (studio_id = public.current_studio_id())
with check (studio_id = public.current_studio_id());

drop policy if exists "owner manages own anamneses" on public.anamneses;
create policy "owner manages own anamneses" on public.anamneses for all
using (studio_id = public.current_studio_id())
with check (studio_id = public.current_studio_id());

drop policy if exists "owner manages own photos" on public.evolution_photos;
create policy "owner manages own photos" on public.evolution_photos for all
using (studio_id = public.current_studio_id())
with check (studio_id = public.current_studio_id());

insert into storage.buckets (id, name, public)
values ('evolution-photos', 'evolution-photos', false)
on conflict (id) do nothing;

drop policy if exists "owner uploads evolution photos" on storage.objects;
create policy "owner uploads evolution photos" on storage.objects for insert to authenticated
with check (bucket_id = 'evolution-photos' and (storage.foldername(name))[1] = auth.uid()::text);

drop policy if exists "owner reads evolution photos" on storage.objects;
create policy "owner reads evolution photos" on storage.objects for select to authenticated
using (bucket_id = 'evolution-photos' and (storage.foldername(name))[1] = auth.uid()::text);

drop policy if exists "owner deletes evolution photos" on storage.objects;
create policy "owner deletes evolution photos" on storage.objects for delete to authenticated
using (bucket_id = 'evolution-photos' and (storage.foldername(name))[1] = auth.uid()::text);
