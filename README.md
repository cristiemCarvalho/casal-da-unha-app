# Casal da Unha

Aplicação mobile-first para gestão de estúdios de alongamento de unhas, construída com Streamlit e Supabase.

## Recursos

- Autenticação por e-mail e senha.
- Isolamento de dados por estúdio com Row Level Security.
- Agenda com serviços, clientes, data, horário e status.
- Lançamento automático de atendimentos concluídos no caixa.
- Catálogo de serviços editável.
- Ficha de anamnese técnica e termo de responsabilidade.
- Galeria privada de evolução visual.
- Tema Rose Gold, fundo visual editável e layout responsivo.

## Executar localmente

Requer Python 3.10 ou superior.

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Copie `.streamlit/secrets.toml.example` para `.streamlit/secrets.toml` e preencha:

```toml
SUPABASE_URL = "https://seu-projeto.supabase.co"
SUPABASE_ANON_KEY = "sua-chave-anon-publica"
APP_URL = "https://seu-app.streamlit.app"
```

Nunca publique `.streamlit/secrets.toml` no GitHub.

Inicie o app:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## Configurar o Supabase

1. Crie um projeto no Supabase.
2. Execute [`supabase_schema.sql`](./supabase_schema.sql) no SQL Editor.
   Se o schema inicial já foi executado, use [`supabase_migration_v2.sql`](./supabase_migration_v2.sql).
3. Configure `SUPABASE_URL` e `SUPABASE_ANON_KEY` nos Secrets do ambiente.
4. Confirme o e-mail da conta criada pela tela de cadastro.
5. Não use a chave `service_role` no Streamlit.

### Confirmação de e-mail

No Supabase, em **Authentication > URL Configuration**:

- **Site URL:** `https://casal-da-unha-app-3dez6inn5hxwnha74hptyx.streamlit.app`
- **Redirect URLs:** adicione a mesma URL.

Em **Authentication > Email Templates > Confirm signup**, use um link de confirmação
com `token_hash`:

```html
<a href="{{ .SiteURL }}/?token_hash={{ .TokenHash }}&type=signup">
  Confirmar meu e-mail
</a>
```

Não use links com `#access_token` para este app: fragmentos são processados apenas
no navegador e não chegam ao Python/Streamlit.

## Publicar no Streamlit Community Cloud

1. Suba este projeto para um repositório GitHub.
2. Crie um app em `share.streamlit.io`.
3. Selecione o repositório, branch e arquivo `app.py`.
4. Em **Settings > Secrets**, adicione:

```toml
SUPABASE_URL = "https://seu-projeto.supabase.co"
SUPABASE_ANON_KEY = "sua-chave-anon-publica"
```

5. Reinicie o app e teste com duas contas diferentes.

## Privacidade

As fichas podem conter dados relacionados à saúde e as fotos são privadas. Antes de disponibilizar o link publicamente, publique uma política de privacidade, colete consentimento adequado e valide as configurações de autenticação e Storage do Supabase.
