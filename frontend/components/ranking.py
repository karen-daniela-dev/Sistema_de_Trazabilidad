"""
components/ranking.py

Componente reutilizable para rankings.
"""

from __future__ import annotations

import streamlit as st


MEDALS = {
    0: "🥇",
    1: "🥈",
    2: "🥉",
}


def show(
    items: list[dict],
    title: str = "Ranking",
    top: int = 10,
):
    """
    Renderiza un ranking vertical.

    Cada elemento debe contener:

    nombre
    score
    """

    st.subheader(title)

    if not items:

        st.info(
            "Sin información."
        )

        return

    maximum = max(
        item["score"]
        for item in items
    )

    maximum = max(
        maximum,
        1,
    )

    for index, item in enumerate(items[:top]):

        medal = MEDALS.get(
            index,
            f"{index + 1}."
        )

        left, right = st.columns(
            [7, 1],
        )

        with left:

            st.markdown(
                f"**{medal} {item['nombre']}**"
            )

            st.progress(
                item["score"] / maximum,
            )

        with right:

            st.metric(
                "Score",
                item["score"],
            )