"""
components/aggrid.py

Componente reutilizable basado en streamlit-aggrid.
"""

from __future__ import annotations

import pandas as pd

from st_aggrid import (
    AgGrid,
    DataReturnMode,
    GridOptionsBuilder,
)


DEFAULT_HEIGHT = 500


# -----------------------------------------------------------------------------
# Configuración
# -----------------------------------------------------------------------------

def _build_grid_options(
    dataframe: pd.DataFrame,
    *,
    hidden_columns: list[str] | None,
    pinned_columns: list[str] | None,
    numeric_columns: list[str] | None,
    column_widths: dict[str, int] | None,
    selection_mode: str,
    selectable: bool,
):
    """
    Construye la configuración de AgGrid.
    """

    ...


# -----------------------------------------------------------------------------
# Renderizado
# -----------------------------------------------------------------------------

def _render_grid(
    dataframe: pd.DataFrame,
    *,
    grid_options: dict,
    key: str,
    height: int,
):
    """
    Renderiza AgGrid.
    """

    return AgGrid(
        dataframe,
        gridOptions=grid_options,
        height=height,
        width="100%",
        data_return_mode=DataReturnMode.AS_INPUT,
        update_on=["selectionChanged"],
        allow_unsafe_jscode=False,
        theme="streamlit",
        key=key,
    )


# -----------------------------------------------------------------------------
# Selección
# -----------------------------------------------------------------------------

def _get_selected_row(
    response,
):
    """
    Retorna la fila seleccionada.
    """

    selected_rows = response.selected_rows

    if (
        selected_rows is None
        or selected_rows.empty
    ):
        return None

    return selected_rows.iloc[0].to_dict()


# -----------------------------------------------------------------------------
# API pública
# -----------------------------------------------------------------------------

def show_table(
    dataframe: pd.DataFrame,
    *,
    key: str,
    height: int = DEFAULT_HEIGHT,
    hidden_columns: list[str] | None = None,
    pinned_columns: list[str] | None = None,
    numeric_columns: list[str] | None = None,
    column_widths: dict[str, int] | None = None,
    selection_mode: str = "single",
    selectable: bool = True,
):
    """
    Renderiza una tabla reutilizable.
    """
    grid_options = _build_grid_options(
        dataframe=dataframe,
        hidden_columns=hidden_columns,
        pinned_columns=pinned_columns,
        numeric_columns=numeric_columns,
        column_widths=column_widths,
        selection_mode=selection_mode,
        selectable=selectable,
    )

    response = _render_grid(
        dataframe=dataframe,
        grid_options=grid_options,
        key=key,
        height=height,
    )

    return _get_selected_row(
        response,
    )    
    
def _build_grid_options(
    dataframe: pd.DataFrame,
    *,
    hidden_columns: list[str] | None,
    pinned_columns: list[str] | None,
    numeric_columns: list[str] | None,
    column_widths: dict[str, int] | None,
    selection_mode: str,
    selectable: bool,
):
    """
    Construye la configuración de AgGrid.
    """

    gb = GridOptionsBuilder.from_dataframe(
        dataframe,
    )

    gb.configure_default_column(
        sortable=True,
        filter=True,
        resizable=True,
    )

    hidden_columns = hidden_columns or []

    pinned_columns = pinned_columns or []

    numeric_columns = numeric_columns or []

    column_widths = column_widths or {}

    for column in dataframe.columns:

        options = {}

        if column in hidden_columns:
            options["hide"] = True

        if column in pinned_columns:
            options["pinned"] = "left"

        if column in numeric_columns:
            options["type"] = ["numericColumn"]

        if column in column_widths:
            options["minWidth"] = column_widths[column]

        if options:
            gb.configure_column(
                column,
                **options,
            )

    if selectable:

        gb.configure_selection(
            selection_mode=selection_mode,
            use_checkbox=False,
        )

    gb.configure_grid_options(
        rowHeight=36,
        headerHeight=38,
        rowSelection=selection_mode if selectable else None,
        suppressRowDeselection=False,
        animateRows=True,
        pagination=False,
    )

    return gb.build()