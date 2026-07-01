"""
components/progress.py

Componentes reutilizables para barras de progreso.
"""

from __future__ import annotations

import streamlit as st


def goal_progress(
    porcentaje: float,
    actual: int,
    meta: int,
    faltantes: int,
):
    """
    Barra de cumplimiento de meta.
    """

    porcentaje = max(
        0,
        min(
            porcentaje,
            100,
        ),
    )

    st.progress(
        porcentaje / 100,
    )

    if faltantes > 0:

        st.caption(
            f"Faltan **{faltantes}** aprendices contratados para alcanzar la meta ({actual}/{meta})."
        )

    else:

        st.success(
            f"Meta alcanzada ({actual}/{meta})."
        )