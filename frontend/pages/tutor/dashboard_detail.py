"""
frontend/pages/tutor/dashboard_detail.py

Información general del aprendiz seleccionado.
"""

from __future__ import annotations

import streamlit as st

from frontend.components.ui import mostrar_semaforo


def show(
    detail: dict,
    compact: bool = False,
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

    if not compact:

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

    c1, c2 = st.columns(2)

    with c1:

        mostrar_semaforo(
            detail["actividad"],
            "Actividad",
        )

    with c2:

        mostrar_semaforo(
            detail["progreso"],
            "Progreso",
        )

    st.divider()