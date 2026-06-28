"""
frontend/pages/tutor
Información general del aprendiz seleccionado por el tutor.
"""

from __future__ import annotations

import streamlit as st


def show(
    detail: dict,
) -> None:
    """
    Muestra la información principal
    del aprendiz seleccionado.
    """

    if not detail:
        return

    st.subheader("👤 Aprendiz seleccionado")

    st.write(
        f"**{detail['nombre']}**"
    )

    st.caption(
        detail["email"]
    )

    c1, c2 = st.columns(2)

    with c1:

        st.write(
            f"📱 {detail.get('telefono') or '-'}"
        )

    with c2:

        st.write(
            f"☎️ {detail.get('telefono_emergencia') or '-'}"
        )

    c1, c2 = st.columns(2)

    c1.metric(
        "Aplicaciones",
        detail["total_aplicaciones"],
    )

    c2.metric(
        "Entrevistas",
        detail["total_entrevistas"],
    )

    st.divider()