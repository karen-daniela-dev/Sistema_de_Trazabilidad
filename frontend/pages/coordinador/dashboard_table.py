"""
pages/coordinador/dashboard_table.py

Tabla principal de tutores del Dashboard del Coordinador.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from frontend.components.aggrid import show_table

from . import dashboard_loader
from . import dashboard_state


PAGE_SIZE = 20


# -----------------------------------------------------------------------------
# DataFrame
# -----------------------------------------------------------------------------

def _prepare_dataframe(
    rows: list[dict],
) -> pd.DataFrame:
    """
    Construye el DataFrame para la tabla.
    """

    dataframe = pd.DataFrame(
        rows,
    )

    dataframe = dataframe[
        [
            "tutor_id",
            "nombre",
            "total_aprendices",
            "contratados",
            "no_contratados",
            "porcentaje_meta",
            "score",
        ]
    ]

    dataframe.rename(

        columns={

            "tutor_id": "id",

            "nombre": "Tutor",

            "total_aprendices": "Aprendices",

            "contratados": "Contratados",

            "no_contratados": "Pendientes",

            "porcentaje_meta": "% Meta",

            "score": "Score",

        },

        inplace=True,

    )

    return dataframe


# -----------------------------------------------------------------------------
# Tabla
# -----------------------------------------------------------------------------

def show(
    cohorte_id: str,
) -> str | None:
    """
    Renderiza la tabla de tutores.
    """

    page = dashboard_loader.load_tutores(

        cohorte_id=cohorte_id,

        page=dashboard_state.get_page(),

        size=PAGE_SIZE,
    )

    if page is None:
        return

    rows = page.get(
        "items",
        [],
    )

    if not rows:

        st.info(
            "No existen tutores para esta cohorte."
        )

        return

    dataframe = _prepare_dataframe(
        rows,
    )

    selected = show_table(

        dataframe=dataframe,

        key="coordinator_tutors",

        hidden_columns=["id"],

        pinned_columns=["Tutor"],

        numeric_columns=[
            "Aprendices",
            "Contratados",
            "Pendientes",
            "Score",
        ],

        column_widths={

            "Tutor": 220,

            "Aprendices": 90,

            "Contratados": 100,

            "Pendientes": 100,

            "% Meta": 90,

            "Score": 80,
        },
    )

    current = dashboard_state.get_selected_tutor()

    if selected is None:
        return current

    if selected["id"] != current:

        dashboard_state.set_selected_tutor(
            selected["id"],
        )

        st.rerun()

    return dashboard_state.get_selected_tutor()