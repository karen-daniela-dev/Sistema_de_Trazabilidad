"""
pages/coordinador/dashboard_apprentice_summary.py

Resumen del aprendiz seleccionado.
"""

from __future__ import annotations

import streamlit as st

from frontend.components.cards import kpi_row
from frontend.components.ui import (
    activity_badge,
    progress_badge,
)
from frontend.components.ui import failure_chart

from frontend import api_client as api

from . import dashboard_state


def show() -> None:
    """
    Renderiza el resumen del aprendiz seleccionado.
    """

    apprentice_id = dashboard_state.get_selected_apprentice()

    if apprentice_id is None:
        return

    data = api.get_coordinator_apprentice(
        apprentice_id,
    )

    if data is None:
        return

    kpi_row(
        [
            {
                "title": "Aplicaciones",
                "value": data["total_aplicaciones"],
            },
            {
                "title": "Entrevistas",
                "value": data["total_entrevistas"],
            },
        ]
    )

    col1, col2 = st.columns(2)

    with col1:

        activity_badge(
            data["actividad"],
        )

    with col2:

        progress_badge(
            data["progreso"],
        )

    st.divider()

    failure_chart(
        data["failure_summary"],
    )