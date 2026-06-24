"""
api_client.py
Cliente HTTP centralizado para comunicar el frontend con la API.
Todas las llamadas pasan por aquí — nunca llamar requests directamente en pages/.
"""
import os
import requests
import streamlit as st

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")
TIMEOUT = 15


def _headers() -> dict:
    token = st.session_state.get("token")
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


def _handle_response(r: requests.Response):
    if r.status_code == 401:
        st.session_state.clear()
        st.error("Sesión expirada. Por favor inicia sesión nuevamente.")
        st.stop()
    if r.status_code == 403:
        try:
            detail = r.json().get("detail", "Sin permisos.")
        except Exception:
            detail = "Sin permisos."
        st.error(detail)
        return None
    if r.status_code == 422:
        try:
            errores = r.json().get("errores", [])
            for e in errores:
                st.error(f"📋 {e.get('campo', '')}: {e.get('mensaje', '')}")
        except Exception:
            st.error(f"Error de validación: {r.text}")
        return None
    if not r.ok:
        try:
            detail = r.json().get("detail", "Error desconocido")
        except Exception:
            detail = r.text or f"Error {r.status_code}"
        st.error(f"❌ {detail}")
        return None
    if not r.content:
        return True
    return r.json()

# ── Auth ──────────────────────────────────────────────────────────────────────

def login(email: str, password: str):
    r = requests.post(f"{API_BASE}/auth/login",
                      data={"username": email, "password": password}, timeout=TIMEOUT)
    return _handle_response(r)


def register_aprendiz(email: str, password: str):
    r = requests.post(f"{API_BASE}/auth/register",
                      json={"email": email, "password": password}, timeout=TIMEOUT)
    return _handle_response(r)


def get_me():
    r = requests.get(f"{API_BASE}/auth/me", headers=_headers(), timeout=TIMEOUT)
    return _handle_response(r)


# ── Cohortes ──────────────────────────────────────────────────────────────────

def get_cohortes():
    r = requests.get(f"{API_BASE}/cohortes/", headers=_headers(), timeout=TIMEOUT)
    return _handle_response(r) or []


def crear_cohorte(data: dict):
    r = requests.post(f"{API_BASE}/cohortes/", json=data, headers=_headers(), timeout=TIMEOUT)
    return _handle_response(r)


# ── Usuarios ──────────────────────────────────────────────────────────────────

def get_tutores():
    r = requests.get(f"{API_BASE}/usuarios/tutores", headers=_headers(), timeout=TIMEOUT)
    return _handle_response(r) or []


def crear_tutor(email: str):
    r = requests.post(f"{API_BASE}/usuarios/tutor", json={"email": email},
                      headers=_headers(), timeout=TIMEOUT)
    return _handle_response(r)


def get_mi_perfil():
    r = requests.get(f"{API_BASE}/usuarios/perfil/me", headers=_headers(), timeout=TIMEOUT)
    if r.status_code == 404:
        return None  # sin perfil aún — no es error
    return _handle_response(r)


def crear_perfil(data: dict):
    r = requests.post(f"{API_BASE}/usuarios/perfil", json=data, headers=_headers(), timeout=TIMEOUT)
    return _handle_response(r)


def actualizar_perfil(data: dict):
    r = requests.patch(f"{API_BASE}/usuarios/perfil/me", json=data,
                       headers=_headers(), timeout=TIMEOUT)
    return _handle_response(r)


# ── Aplicaciones ──────────────────────────────────────────────────────────────

def get_aplicaciones(page=1, size=20):
    r = requests.get(f"{API_BASE}/aplicaciones/", params={"page": page, "size": size},
                     headers=_headers(), timeout=TIMEOUT)
    return _handle_response(r)


def crear_aplicacion(data: dict):
    r = requests.post(f"{API_BASE}/aplicaciones/", json=data, headers=_headers(), timeout=TIMEOUT)
    return _handle_response(r)


def marcar_contratado(app_id: str):
    r = requests.post(f"{API_BASE}/aplicaciones/marcar-contratado",
                      json={"aplicacion_id": app_id}, headers=_headers(), timeout=TIMEOUT)
    return _handle_response(r)


def eliminar_aplicacion(app_id: str):
    r = requests.delete(f"{API_BASE}/aplicaciones/{app_id}", headers=_headers(), timeout=TIMEOUT)
    return r.status_code == 204


# ── Entrevistas ───────────────────────────────────────────────────────────────

def get_entrevistas(app_id: str):
    r = requests.get(f"{API_BASE}/entrevistas/por-aplicacion/{app_id}",
                     headers=_headers(), timeout=TIMEOUT)
    return _handle_response(r) or []


def crear_entrevista(data: dict):
    r = requests.post(f"{API_BASE}/entrevistas/", json=data, headers=_headers(), timeout=TIMEOUT)
    return _handle_response(r)


# ── KPIs ──────────────────────────────────────────────────────────────────────

def get_kpis_personal():
    r = requests.get(f"{API_BASE}/kpis/personal", headers=_headers(), timeout=TIMEOUT)
    return _handle_response(r)


def get_kpis_grupo():
    r = requests.get(f"{API_BASE}/kpis/grupo", headers=_headers(), timeout=TIMEOUT)
    return _handle_response(r)


def get_kpis_globales():
    r = requests.get(f"{API_BASE}/kpis/global", headers=_headers(), timeout=TIMEOUT)
    return _handle_response(r)


def get_alertas():
    r = requests.get(f"{API_BASE}/kpis/alertas", headers=_headers(), timeout=TIMEOUT)
    return _handle_response(r) or []


def marcar_alerta_leida(alerta_id: str):
    r = requests.patch(f"{API_BASE}/kpis/alertas/{alerta_id}/leer",
                       headers=_headers(), timeout=TIMEOUT)
    return _handle_response(r)
