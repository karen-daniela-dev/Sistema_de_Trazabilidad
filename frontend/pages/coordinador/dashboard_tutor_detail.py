"""
pages/coordinador/dashboard_tutor_detail.py

Tabla de aprendices del tutor seleccionado.
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from frontend.components.aggrid import show_table

from . import dashboard_loader
from . import dashboard_state


PAGE_SIZE = 20


# -----------------------------------------------------------------------------
# Utilidades
# -----------------------------------------------------------------------------

def _semaphore_icon(
    estado: str,
) -> str:

    icons = {
        "GREEN": "🟢",
        "YELLOW": "🟡",
        "RED": "🔴",
        "INSUFFICIENT_DATA": "⚪",
    }

    return icons.get(
        estado,
        "⚪",
    )


def _format_date(
    value: datetime | str | None,
) -> str:

    if value is None:
        return "-"

    if isinstance(
        value,
        datetime,
    ):
        return value.strftime(
            "%d/%m/%Y",
        )

    try:

        return datetime.fromisoformat(
            value.replace(
                "Z",
                "+00:00",
            )
        ).strftime(
            "%d/%m/%Y",
        )

    except Exception:

        return "-"


# -----------------------------------------------------------------------------
# DataFrame
# -----------------------------------------------------------------------------

def _prepare_dataframe(
    rows: list[dict],
) -> pd.DataFrame:

    dataframe = pd.DataFrame(
        rows,
    )

    dataframe["actividad"] = dataframe[
        "actividad"
    ].map(
        _semaphore_icon,
    )

    dataframe["progreso"] = dataframe[
        "progreso"
    ].map(
        _semaphore_icon,
    )

    dataframe["contratado"] = dataframe[
        "contratado"
    ].map(
        lambda x: "✅" if x else "—",
    )

    dataframe["ultima_actividad"] = dataframe[
        "ultima_actividad"
    ].map(
        _format_date,
    )

    dataframe = dataframe[
        [
            "id",
            "nombre",
            "total_aplicaciones",
           
            "actividad",
            "progreso",
            "contratado",
            "ultima_actividad",
        ]
    ]

    dataframe.rename(

        columns={

            "nombre": "Aprendiz",

            "total_aplicaciones": "Apps",

            

            "actividad": "Actividad",

            "progreso": "Progreso",

            "contratado": "✔",

            "ultima_actividad": "Última actividad",
        },

        inplace=True,
    )

    return dataframe


# -----------------------------------------------------------------------------
# Tabla
# -----------------------------------------------------------------------------

def show(
    cohorte_id: str,
    tutor_id: str,
) -> None:

    detail = dashboard_loader.load_tutor_detail(

        cohorte_id=cohorte_id,

        tutor_id=tutor_id,

        page=dashboard_state.get_tutor_page(),

        size=PAGE_SIZE,
    )

    if detail is None:
        return

    st.subheader(
        f"Aprendices del tutor: {detail['nombre']}"
    )

    page = detail["aprendices"]

    rows = page.get(
        "items",
        [],
    )

    if not rows:

        st.info(
            "Este tutor no tiene aprendices."
        )

        return
    st.write(detail["nombre"])
    st.write(len(rows))
    st.write(rows[:3])

    dataframe = _prepare_dataframe(
        rows,
    )

    selected = show_table(

        dataframe=dataframe,

        key="coordinator_apprentices",

        hidden_columns=["id"],

        pinned_columns=["Aprendiz"],

        numeric_columns=[
            "Apps",
            
        ],

        column_widths={
            "Aprendiz": 220,
            "Apps": 80,
         
        },
    )

    current = dashboard_state.get_selected_apprentice()

    if selected is None:
        return current

    if selected["id"] != current:

        dashboard_state.set_selected_apprentice(
            selected["id"],
        )

        return selected["id"]

    return current