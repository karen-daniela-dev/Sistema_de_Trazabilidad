"""
pages/coordinador/dashboard_state.py

Estado del Dashboard del Coordinador.
"""

from __future__ import annotations

import streamlit as st


# -----------------------------------------------------------------------------
# Inicialización
# -----------------------------------------------------------------------------

def init_state() -> None:

    st.session_state.setdefault(
        "coordinator_page",
        1,
    )

    st.session_state.setdefault(
        "selected_cohort",
        None,
    )

    st.session_state.setdefault(
        "selected_tutor",
        None,
    )

    st.session_state.setdefault(
        "selected_tutor_page",
        1,
    )


# -----------------------------------------------------------------------------
# Cohorte
# -----------------------------------------------------------------------------

def get_selected_cohort():

    return st.session_state.get(
        "selected_cohort",
    )


def set_selected_cohort(
    cohorte_id,
):

    st.session_state["selected_cohort"] = cohorte_id

    st.session_state["selected_tutor"] = None

    st.session_state["selected_tutor_page"] = 1

    st.session_state["coordinator_page"] = 1


# -----------------------------------------------------------------------------
# Tutor
# -----------------------------------------------------------------------------

def get_selected_tutor():

    return st.session_state.get(
        "selected_tutor",
    )


def set_selected_tutor(
    tutor_id,
):

    st.session_state["selected_tutor"] = tutor_id

    st.session_state["selected_tutor_page"] = 1


# -----------------------------------------------------------------------------
# Paginación
# -----------------------------------------------------------------------------

def get_page():

    return st.session_state["coordinator_page"]


def set_page(
    page: int,
):

    st.session_state["coordinator_page"] = page


def get_tutor_page():

    return st.session_state["selected_tutor_page"]


def set_tutor_page(
    page: int,
):

    st.session_state["selected_tutor_page"] = page
    
# -----------------------------------------------------------------------------
# Aprendiz
# -----------------------------------------------------------------------------

def get_selected_apprentice():

    return st.session_state.get(
        "selected_apprentice",
    )


def set_selected_apprentice(
    apprentice_id,
):

    st.session_state["selected_apprentice"] = apprentice_id   