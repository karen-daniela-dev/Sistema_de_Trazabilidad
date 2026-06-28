"""
pages/tutor/dashboard_failures.py

Gráficos de fallas del Dashboard Tutor.
"""

from __future__ import annotations

import streamlit as st
import plotly.graph_objects as go


# Colores reutilizados en todas las tortas

PIE_COLORS = [
    "#3b82f6",
    "#10b981",
    "#f59e0b",
    "#ef4444",
    "#8b5cf6",
    "#06b6d4",
    "#ec4899",
    "#84cc16",
]


# -----------------------------------------------------------------------------
# Panel principal
# -----------------------------------------------------------------------------

def show(
    summary: dict,
) -> None:
    """
    Renderiza las tortas de fallas
    del aprendiz seleccionado.
    """

    if not summary:

        return

    pies = summary.get(
        "pies",
        [],
    )

    if not pies:

        st.info(
            "Este aprendiz aún no registra fallas."
        )

        return

    st.subheader(
        "📊 Análisis de fallas"
    )

    columns = st.columns(2)

    for index, pie in enumerate(pies):

        with columns[index % 2]:

            st.plotly_chart(
                _build_pie(
                    pie,
                ),
                use_container_width=True,
            )


# -----------------------------------------------------------------------------
# Construcción de una torta
# -----------------------------------------------------------------------------

def _build_pie(
    pie: dict,
) -> go.Figure:
    """
    Construye una gráfica de torta
    para una categoría de falla.
    """

    elementos = pie.get(
        "elementos",
        [],
    )

    if not elementos:

        figure = go.Figure(
            go.Pie(
                labels=["Sin registros"],
                values=[1],
                hole=0.45,
                marker_colors=["#e5e7eb"],
                textinfo="label",
                hoverinfo="skip",
            )
        )

    else:

        labels = [
            item["nombre"]
            for item in elementos
        ]

        values = [
            item["cantidad"]
            for item in elementos
        ]

        figure = go.Figure(
            go.Pie(
                labels=labels,
                values=values,
                hole=0.45,
                marker_colors=PIE_COLORS[:len(labels)],
                textinfo="label+percent",
                hovertemplate=(
                    "<b>%{label}</b>"
                    "<br>Ocurrencias: %{value}"
                    "<extra></extra>"
                ),
            )
        )

    figure.update_layout(

        title=dict(
            text=pie["titulo"],
            font=dict(
                size=15,
            ),
        ),

        height=300,

        margin=dict(
            l=10,
            r=10,
            t=50,
            b=10,
        ),

        showlegend=False,

        paper_bgcolor="rgba(0,0,0,0)",
    )

    return figure