-- Persistência da identidade visual do estúdio.

alter table public.studios add column if not exists logo_path text;
alter table public.studios add column if not exists background_path text;
alter table public.studios add column if not exists background_opacity numeric(3,2) not null default 0.92;

insert into storage.buckets (id, name, public)
values ('studio-assets', 'studio-assets', false)
on conflict (id) do nothing;

drop policy if exists "owner uploads studio assets" on storage.objects;
create policy "owner uploads studio assets" on storage.objects for insert to authenticated
with check (
    bucket_id = 'studio-assets'
    and (storage.foldername(name))[1] = auth.uid()::text
);

drop policy if exists "owner reads studio assets" on storage.objects;
create policy "owner reads studio assets" on storage.objects for select to authenticated
using (
    bucket_id = 'studio-assets'
    and (storage.foldername(name))[1] = auth.uid()::text
);

drop policy if exists "owner updates studio assets" on storage.objects;
create policy "owner updates studio assets" on storage.objects for update to authenticated
using (
    bucket_id = 'studio-assets'
    and (storage.foldername(name))[1] = auth.uid()::text
)
with check (
    bucket_id = 'studio-assets'
    and (storage.foldername(name))[1] = auth.uid()::text
);
