"""
components/cards.py

Tarjetas KPI reutilizables.
"""

from __future__ import annotations

import streamlit as st


def kpi_card(
    title: str,
    value,
    subtitle: str = "",
    color: str = "#2563eb",
):
    """
    Tarjeta KPI utilizando únicamente
    componentes nativos de Streamlit.
    """

    with st.container(border=True):

        st.caption(title)

        st.metric(
            label="",
            value=value,
        )

        if subtitle:

            st.caption(subtitle)


def kpi_row(
    cards: list[dict],
):
    """
    Renderiza una fila de KPIs.
    """

    columns = st.columns(len(cards))

    for column, card in zip(columns, cards):

        with column:

            kpi_card(
                title=card["title"],
                value=card["value"],
                subtitle=card.get(
                    "subtitle",
                    "",
                ),
                color=card.get(
                    "color",
                    "#2563eb",
                ),
            )