"""
cohorte_selector.py

Selector maestro de Cohortes.

Este componente controla el contexto del Dashboard del Coordinador.

Responsabilidades:

- Obtener cohortes (usa api_client cacheado)
- Ordenarlas para dashboard
- Seleccionar cohorte
- Persistir selección
- Mostrar información resumida

NO carga KPIs.
NO consulta tutores.
NO consulta aprendices.
"""

from __future__ import annotations

from datetime import date

import streamlit as st

from frontend import api_client as api
from frontend.components import dashboard_state_coor


# ======================================================================
# Configuración visual
# ======================================================================

_ESTADO_ICON = {
    "ACTIVA": "🟢",
    "FINALIZADA": "⚪",
    "INACTIVA": "⚫",
}


# ======================================================================
# Helpers
# ======================================================================

def _priority(cohorte: dict) -> tuple:
    """
    Orden enterprise.

    1 ACTIVA
    2 FINALIZADA
    3 INACTIVA

    Dentro del grupo:
        fecha_inicio DESC
    """

    estado = cohorte["estado"]

    prioridad = {
        "ACTIVA": 0,
        "FINALIZADA": 1,
        "INACTIVA": 2,
    }.get(estado, 99)

    return (
        prioridad,
        cohorte["fecha_inicio"],
    )


def _build_label(cohorte: dict) -> str:

    icono = _ESTADO_ICON.get(cohorte["estado"], "⚪")

    return (
        f"{icono} "
        f"{cohorte['nombre']}   "
        f"({cohorte['estado']})"
    )


def _dias_restantes(cohorte: dict) -> int:

    try:

        hoy = date.today()

        fin = date.fromisoformat(cohorte["fecha_fin"])

        return (fin - hoy).days

    except Exception:

        return 0


# ======================================================================
# Selector
# ======================================================================

def render() -> dict | None:
    """
    Renderiza el selector.

    Retorna siempre la cohorte activa.
    """

    cohortes = api.get_cohortes()

    if not cohortes:

        st.warning("No existen cohortes registradas.")

        return None

    cohortes = sorted(
        cohortes,
        key=_priority,
        reverse=False,
    )

    labels = [
        _build_label(c)
        for c in cohortes
    ]

    actual = dashboard_state_coor.get_cohorte()

    default_index = 0

    if actual:

        for i, cohorte in enumerate(cohortes):

            if cohorte["id"] == actual["id"]:

                default_index = i

                break

    st.markdown("### 🎓 Cohorte de trabajo")

    selected_index = st.selectbox(
        label="",
        options=range(len(cohortes)),
        index=default_index,
        format_func=lambda i: labels[i],
        label_visibility="collapsed",
    )

    seleccionada = cohortes[selected_index]

    dashboard_state_coor.set_cohorte(seleccionada)

    _render_resume(seleccionada)

    return seleccionada


# ======================================================================
# Panel Resumen
# ======================================================================

def _render_resume(cohorte: dict):

    dias = _dias_restantes(cohorte)

    with st.container(border=True):

        c1, c2 = st.columns(2)

        with c1:

            st.caption("Estado")

            st.write(
                _ESTADO_ICON.get(
                    cohorte["estado"],
                    "⚪"
                ),
                cohorte["estado"],
            )

            st.caption("Inicio")

            st.write(cohorte["fecha_inicio"])

        with c2:

            st.caption("Fin")

            st.write(cohorte["fecha_fin"])

            st.caption("Meta")

            st.metric(
                "",
                cohorte["meta_contratacion"],
            )

        if cohorte["estado"] == "ACTIVA":

            if dias >= 0:

                st.info(
                    f"Quedan **{dias} días** para finalizar la cohorte."
                )

            else:

                st.warning(
                    "La cohorte superó su fecha de finalización."
                )