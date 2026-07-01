"""
dashboard_selection_state.py

Estado centralizado del Dashboard del Coordinador.

Single Source of Truth para todos los filtros del dashboard.

Ningún componente debe acceder directamente a
st.session_state["..."].

Siempre usar las funciones expuestas aquí.
"""

from __future__ import annotations

from typing import Any

import streamlit as st


# ======================================================================
# Session Keys
# ======================================================================

COHORTE_KEY = "dashboard_selected_cohorte"

TUTOR_KEY = "dashboard_selected_tutor"

APRENDIZ_KEY = "dashboard_selected_aprendiz"


# ======================================================================
# Cohorte
# ======================================================================

def get_cohorte() -> dict | None:
    """
    Retorna la cohorte actualmente seleccionada.
    """
    return st.session_state.get(COHORTE_KEY)


def get_cohorte_id() -> str | None:
    """
    Retorna únicamente el id de la cohorte.
    """
    cohorte = get_cohorte()

    if cohorte is None:
        return None

    return str(cohorte["id"])


def set_cohorte(cohorte: dict) -> None:
    """
    Cambia la cohorte activa.

    Cuando cambia la cohorte se reinician
    automáticamente tutor y aprendiz.
    """

    actual = get_cohorte()

    if actual and actual["id"] == cohorte["id"]:
        return

    st.session_state[COHORTE_KEY] = cohorte

    clear_tutor()

    clear_aprendiz()


def clear_cohorte() -> None:
    st.session_state.pop(COHORTE_KEY, None)

    clear_tutor()

    clear_aprendiz()


# ======================================================================
# Tutor
# ======================================================================

def get_tutor() -> dict | None:
    return st.session_state.get(TUTOR_KEY)


def get_tutor_id() -> str | None:
    tutor = get_tutor()

    if tutor is None:
        return None

    return str(tutor["tutor_id"])


def set_tutor(tutor: dict) -> None:

    actual = get_tutor()

    if actual and actual["tutor_id"] == tutor["tutor_id"]:
        return

    st.session_state[TUTOR_KEY] = tutor

    clear_aprendiz()


def clear_tutor() -> None:
    st.session_state.pop(TUTOR_KEY, None)

    clear_aprendiz()


# ======================================================================
# Aprendiz
# ======================================================================

def get_aprendiz() -> dict | None:
    return st.session_state.get(APRENDIZ_KEY)


def get_aprendiz_id() -> str | None:

    aprendiz = get_aprendiz()

    if aprendiz is None:
        return None

    return str(aprendiz["usuario_id"])


def set_aprendiz(aprendiz: dict) -> None:

    actual = get_aprendiz()

    if actual and actual["usuario_id"] == aprendiz["usuario_id"]:
        return

    st.session_state[APRENDIZ_KEY] = aprendiz


def clear_aprendiz() -> None:
    st.session_state.pop(APRENDIZ_KEY, None)


# ======================================================================
# Helpers
# ======================================================================

def reset_dashboard() -> None:
    """
    Reinicia completamente el estado del dashboard.
    """

    clear_cohorte()

    clear_tutor()

    clear_aprendiz()


def has_selected_cohorte() -> bool:
    return get_cohorte() is not None


def has_selected_tutor() -> bool:
    return get_tutor() is not None


def has_selected_aprendiz() -> bool:
    return get_aprendiz() is not None


# ======================================================================
# Debug
# ======================================================================

def debug() -> dict[str, Any]:
    """
    Solo para desarrollo.
    """

    return {
        "cohorte": get_cohorte(),
        "tutor": get_tutor(),
        "aprendiz": get_aprendiz(),
    }