"""
pages/coordinador/dashboard_summary.py

Resumen superior del Dashboard del Coordinador.
"""

from __future__ import annotations

import streamlit as st

from frontend.components.cards import (
    kpi_row,
)



from frontend.components.progress import (
    goal_progress,
)

from . import dashboard_loader


def show(
    cohorte_id: str,
) -> None:
    """
    Renderiza el resumen superior del dashboard.
    """
    #st.write(kpi_row.__module__)
    summary = dashboard_loader.load_summary(
        cohorte_id,
    )

    if summary is None:
        return

    st.markdown("### Cumplimiento de la meta")

    goal_progress(

        porcentaje=summary["goal"]["porcentaje_cumplimiento"],

        actual=summary["goal"]["contratados"],

        meta=summary["goal"]["meta_contratados"],

        faltantes=summary["goal"]["faltantes"],
    )

    cards = [

        {
            "title": "Aprendices",

            "value": summary["cards"]["total_aprendices"],
        },

        {
            "title": "Contratados",

            "value": summary["cards"]["contratados"],

            "color": "#16a34a",
        },

        {
            "title": "No contratados",

            "value": summary["cards"]["no_contratados"],

            "color": "#dc2626",
        },
    ]

    kpi_row(
        cards,
    )

