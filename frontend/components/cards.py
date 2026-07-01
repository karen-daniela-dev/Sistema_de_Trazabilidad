"""
components/cards.py

Tarjetas reutilizables para dashboards.
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
    Tarjeta KPI estándar.
    """

    st.markdown(
        f"""
        <div style="
            background:white;
            border:1px solid #e5e7eb;
            border-radius:12px;
            padding:18px;
            text-align:center;
            box-shadow:0 1px 3px rgba(0,0,0,.08);
        ">

            <div style="
                font-size:0.85rem;
                color:#6b7280;
                margin-bottom:8px;
            ">
                {title}
            </div>

            <div style="
                font-size:2rem;
                font-weight:700;
                color:{color};
            ">
                {value}
            </div>

            <div style="
                color:#9ca3af;
                font-size:.8rem;
                margin-top:6px;
            ">
                {subtitle}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_row(
    cards: list[dict],
):
    """
    Renderiza una fila de tarjetas KPI.
    """

    columns = st.columns(len(cards))

    for col, card in zip(columns, cards):

        with col:

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