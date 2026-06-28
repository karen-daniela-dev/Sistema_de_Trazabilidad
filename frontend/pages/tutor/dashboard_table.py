"""
pages/tutor/dashboard_table.py

Tabla principal del Dashboard del Tutor.
version = streamlit-aggrid 1.2.1.post2.
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from st_aggrid import (
    AgGrid,
    DataReturnMode,
    GridOptionsBuilder,
)

GRID_HEIGHT = 500


# -----------------------------------------------------------------------------
# Utilidades
# -----------------------------------------------------------------------------

def _semaphore_icon(
    estado: str,
) -> str:
    """
    Convierte el estado
    en un indicador visual.
    """

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
    """
    Formatea una fecha.
    """

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
    """
    Construye el DataFrame
    para AgGrid.
    """

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
            "telefono",
            "telefono_emergencia",
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

            "telefono": "Teléfono",

            "telefono_emergencia": "Emergencia",

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
# Tabla principal
# -----------------------------------------------------------------------------

def show(
    page: dict,
) -> None:
    """
    Renderiza la tabla principal
    de aprendices.
    """

    rows = page.get(
        "items",
        [],
    )

    if not rows:

        st.info(
            "No existen aprendices asignados."
        )

        return

    dataframe = _prepare_dataframe(
        rows,
    )

    gb = GridOptionsBuilder.from_dataframe(
        dataframe,
    )

    gb.configure_default_column(
        sortable=True,
        filter=True,
        resizable=True,
    )

    gb.configure_column(
        "id",
        hide=True,
    )

    gb.configure_column(
        "Aprendiz",
        pinned="left",
        minWidth=220,
    )

    gb.configure_column(
        "Teléfono",
        minWidth=120,
    )

    gb.configure_column(
        "Emergencia",
        minWidth=120,
    )

    gb.configure_column(
        "Apps",
        maxWidth=80,
        type=["numericColumn"],
    )

    gb.configure_column(
        "Actividad",
        maxWidth=90,
    )

    gb.configure_column(
        "Progreso",
        maxWidth=90,
    )

    gb.configure_column(
        "✔",
        maxWidth=70,
    )

    gb.configure_column(
        "Última actividad",
        minWidth=130,
    )

    gb.configure_selection(
        selection_mode="single",
        use_checkbox=False,
    )

    gb.configure_grid_options(

        rowHeight=36,

        headerHeight=38,

        rowSelection="single",

        suppressRowDeselection=False,

        animateRows=True,

        pagination=False,
    )

    response = AgGrid(

        dataframe,

        gridOptions=gb.build(),

        height=GRID_HEIGHT,

        width="100%",

        data_return_mode=DataReturnMode.AS_INPUT,

        update_on=["selectionChanged"],

        allow_unsafe_jscode=False,

        theme="streamlit",
        
        key="tutor_apprentices_grid",
    )
    
   

    selected_rows = response.selected_rows

    if (
        selected_rows is None
        or selected_rows.empty
    ):

        return

    apprentice_id = selected_rows.iloc[0]["id"]

    current_apprentice = st.session_state.get(
        "selected_apprentice",
    )

    if apprentice_id == current_apprentice:

        return

    st.session_state[
        "selected_apprentice"
    ] = apprentice_id

    st.session_state[
        "selected_panel"
    ] = None

    st.rerun()
    