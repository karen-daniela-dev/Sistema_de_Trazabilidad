"""
pages/coordinador/dashboard_ranking.py

Ranking de tutores.
"""

from __future__ import annotations

import streamlit as st

from frontend.components.ranking import show as show_ranking

from . import dashboard_loader


def show(
    cohorte_id: str,
) -> None:
    """
    Renderiza el ranking de tutores.
    """

    ranking = dashboard_loader.load_ranking(
        cohorte_id,
    )

    if not ranking:

        st.info(
            "No hay información para generar el ranking."
        )

        return

    show_ranking(

        items=ranking,

        title="🏆 Ranking de tutores",

        top=10,
    )