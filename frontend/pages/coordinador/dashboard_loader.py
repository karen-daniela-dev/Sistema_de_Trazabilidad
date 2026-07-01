"""
pages/coordinador/dashboard_loader.py

Carga de datos para el Dashboard del Coordinador.

Centraliza todas las llamadas al backend para
mantener desacoplada la capa visual.
"""

from __future__ import annotations

import streamlit as st

from frontend import api_client as api


PAGE_SIZE = 20


# -----------------------------------------------------------------------------
# Cohortes
# -----------------------------------------------------------------------------

@st.cache_data(
    ttl=300,
    show_spinner=False,
)
def load_cohortes() -> list[dict]:
    """
    Carga las cohortes disponibles.
    """

    return api.get_coordinator_cohortes()


# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------

@st.cache_data(
    ttl=60,
    show_spinner=False,
)
def load_summary(
    cohorte_id: str,
) -> dict | None:
    """
    Carga las tarjetas superiores.
    """

    return api.get_coordinator_summary(
        cohorte_id,
    )


# -----------------------------------------------------------------------------
# Ranking
# -----------------------------------------------------------------------------

@st.cache_data(
    ttl=60,
    show_spinner=False,
)
def load_ranking(
    cohorte_id: str,
) -> list[dict]:
    """
    Carga el ranking de tutores.
    """

    return api.get_coordinator_ranking(
        cohorte_id,
    )


# -----------------------------------------------------------------------------
# Tabla de tutores
# -----------------------------------------------------------------------------

def load_tutores(
    cohorte_id: str,
    page: int,
    size: int = PAGE_SIZE,
):
    """
    Carga la tabla paginada
    de tutores.
    """

    return api.get_coordinator_tutors(
        cohorte_id=cohorte_id,
        page=page,
        size=size,
    )


# -----------------------------------------------------------------------------
# Detalle del tutor
# -----------------------------------------------------------------------------

def load_tutor_detail(
    cohorte_id: str,
    tutor_id: str,
    page: int,
    size: int = PAGE_SIZE,
):
    """
    Carga la tabla de aprendices
    del tutor seleccionado.
    """

    return api.get_coordinator_tutor_detail(
        cohorte_id=cohorte_id,
        tutor_id=tutor_id,
        page=page,
        size=size,
    )