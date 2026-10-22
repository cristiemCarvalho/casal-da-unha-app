from __future__ import annotations

from typing import Any

import streamlit as st


def get_supabase_client() -> Any | None:
    """Create a Supabase client from Streamlit secrets when configured."""
    try:
        url = st.secrets["SUPABASE_URL"]
        anon_key = st.secrets["SUPABASE_ANON_KEY"]
    except (KeyError, FileNotFoundError):
        return None

    try:
        from supabase import create_client
    except ImportError as error:
        raise RuntimeError(
            "A dependência supabase está ausente. Instale as dependências do projeto."
        ) from error

    client = create_client(url, anon_key)
    auth_session = st.session_state.get("supabase_session")
    if auth_session:
        client.auth.set_session(
            auth_session["access_token"],
            auth_session["refresh_token"],
        )
    return client


def is_configured() -> bool:
    return get_supabase_client() is not None


def sign_in(email: str, password: str) -> tuple[Any | None, str | None]:
    client = get_supabase_client()
    if client is None:
        return None, "Configure SUPABASE_URL e SUPABASE_ANON_KEY nos Secrets."
    try:
        response = client.auth.sign_in_with_password(
            {"email": email.strip(), "password": password}
        )
        if response.session is None:
            return None, "O Supabase não retornou uma sessão válida para este login."
        st.session_state.supabase_session = {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
        }
        return response.user, None
    except Exception as error:
        return None, f"Não foi possível entrar: {error}"


def app_url() -> str:
    try:
        return st.secrets["APP_URL"].rstrip("/")
    except (KeyError, FileNotFoundError):
        return "http://localhost:8501"


def sign_up(email: str, password: str) -> tuple[Any | None, str | None]:
    client = get_supabase_client()
    if client is None:
        return None, "Configure SUPABASE_URL e SUPABASE_ANON_KEY nos Secrets."
    try:
        response = client.auth.sign_up(
            {
                "email": email.strip(),
                "password": password,
                "options": {"email_redirect_to": app_url()},
            }
        )
        if response.session is not None:
            st.session_state.supabase_session = {
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
            }
        return response.user, None
    except Exception as error:
        return None, f"Não foi possível criar a conta: {error}"


def verify_email_token(token_hash: str, token_type: str = "signup") -> tuple[Any | None, str | None]:
    client = get_supabase_client()
    if client is None:
        return None, "Configure SUPABASE_URL e SUPABASE_ANON_KEY nos Secrets."
    try:
        response = client.auth.verify_otp(
            {"token_hash": token_hash, "type": token_type}
        )
        if response.session is None:
            return None, "O Supabase não retornou uma sessão após a confirmação."
        st.session_state.supabase_session = {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
        }
        return response.user, None
    except Exception:
        return None, "Não foi possível confirmar o e-mail. Solicite um novo link."


def sign_out() -> None:
    client = get_supabase_client()
    if client is not None:
        client.auth.sign_out()
    st.session_state.pop("supabase_session", None)


def current_user_id() -> str | None:
    client = get_supabase_client()
    if client is None:
        return None
    user = client.auth.get_user().user
    return user.id if user is not None else None


def ensure_studio(name: str = "Meu Studio", primary_color: str = "#E91E63") -> dict[str, Any]:
    client = get_supabase_client()
    if client is None:
        raise RuntimeError("Supabase não está configurado.")
    user_id = current_user_id()
    if user_id is None:
        raise RuntimeError("Sessão Supabase expirada. Faça login novamente.")
    result = client.rpc("create_studio_for_user").execute()
    if not result.data:
        raise RuntimeError("Não foi possível criar ou recuperar o estúdio da usuária.")
    studio = result.data[0] if isinstance(result.data, list) else result.data
    updates = {}
    if studio.get("name") == "Meu Studio" and name.strip():
        updates["name"] = name.strip()
    if primary_color:
        updates["primary_color"] = primary_color
    if updates:
        result = client.table("studios").update(updates).eq("id", studio["id"]).execute()
        studio = result.data[0] if result.data else {**studio, **updates}
    return studio


def load_workspace() -> dict[str, Any]:
    client = get_supabase_client()
    if client is None:
        raise RuntimeError("Supabase não está configurado.")
    studio = ensure_studio()
    studio_id = studio["id"]
    data = {"studio": studio, "clients": [], "services": [], "appointments": [], "cash": [], "anamneses": [], "photos": []}
    queries = {
        "clients": client.table("clients").select("*").eq("studio_id", studio_id).order("name").execute(),
        "services": client.table("services").select("*").eq("studio_id", studio_id).order("name").execute(),
        "appointments": client.table("appointments").select("*").eq("studio_id", studio_id).order("appointment_date").order("appointment_time").execute(),
        "cash": client.table("cash_entries").select("*").eq("studio_id", studio_id).order("created_at", desc=True).execute(),
        "anamneses": client.table("anamneses").select("*").eq("studio_id", studio_id).execute(),
        "photos": client.table("evolution_photos").select("*").eq("studio_id", studio_id).execute(),
    }
    for key, result in queries.items():
        data[key] = result.data or []
    return data


def insert_row(table: str, row: dict[str, Any]) -> dict[str, Any]:
    client = get_supabase_client()
    if client is None:
        raise RuntimeError("Supabase não está configurado.")
    result = client.table(table).insert(row).execute()
    if not result.data:
        raise RuntimeError(f"Não foi possível salvar o registro em {table}.")
    return result.data[0]


def update_row(table: str, row_id: str, updates: dict[str, Any]) -> dict[str, Any]:
    client = get_supabase_client()
    if client is None:
        raise RuntimeError("Supabase não está configurado.")
    result = client.table(table).update(updates).eq("id", row_id).execute()
    if not result.data:
        raise RuntimeError(f"Não foi possível atualizar o registro em {table}.")
    return result.data[0]


def upsert_row(table: str, row: dict[str, Any], on_conflict: str) -> dict[str, Any]:
    client = get_supabase_client()
    if client is None:
        raise RuntimeError("Supabase não está configurado.")
    result = client.table(table).upsert(row, on_conflict=on_conflict).execute()
    if not result.data:
        raise RuntimeError(f"Não foi possível salvar o registro em {table}.")
    return result.data[0]


def delete_row(table: str, row_id: str) -> None:
    client = get_supabase_client()
    if client is None:
        raise RuntimeError("Supabase não está configurado.")
    client.table(table).delete().eq("id", row_id).execute()


def upload_photo(path: str, content: bytes, content_type: str) -> str:
    client = get_supabase_client()
    if client is None:
        raise RuntimeError("Supabase não está configurado.")
    client.storage.from_("evolution-photos").upload(
        path, content, {"content-type": content_type, "upsert": "true"}
    )
    return client.storage.from_("evolution-photos").create_signed_url(path, 3600)["signedURL"]


def signed_photo_url(path: str) -> str:
    client = get_supabase_client()
    if client is None:
        raise RuntimeError("Supabase não está configurado.")
    return client.storage.from_("evolution-photos").create_signed_url(path, 3600)["signedURL"]
