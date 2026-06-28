"""
pages/tutor/dashboard_reflections.py

Reflexiones del aprendiz seleccionado.
"""

from __future__ import annotations

from datetime import datetime

import streamlit as st

from frontend import api_client as api


PAGE_SIZE = 20


# -----------------------------------------------------------------------------
# Panel principal
# -----------------------------------------------------------------------------

def show(
    aprendiz_id: str,
) -> None:
    """
    Muestra las reflexiones
    del aprendiz seleccionado.
    """

    if not aprendiz_id:

        return

    state_key = f"reflections_page_{aprendiz_id}"

    if state_key not in st.session_state:

        st.session_state[state_key] = 1

    page = api.get_tutor_reflections(
        aprendiz_id=aprendiz_id,
        page=st.session_state[state_key],
        size=PAGE_SIZE,
    )

    if page is None:

        return

    st.subheader(
        "💭 Reflexiones"
    )

    rows = page.get(
        "items",
        [],
    )

    if not rows:

        st.info(
            "Este aprendiz aún no registra reflexiones."
        )

        return

    for row in rows:

        _render_reflection(
            row,
        )

    _render_pagination(
        page,
        state_key,
    )


# -----------------------------------------------------------------------------
# Reflexión
# -----------------------------------------------------------------------------

def _render_reflection(
    row: dict,
) -> None:
    """
    Renderiza una reflexión.
    """

    with st.container():

        col1, col2 = st.columns(
            [
                3,
                1,
            ]
        )

        with col1:

            st.markdown(
                f"**{row['empresa']}** — {row['vacante']}"
            )

            st.caption(
                f"{_format_date(row['fecha'])} · {row['tipo_entrevista']}"
            )

        with col2:

            if row.get(
                "autoevaluacion"
            ):

                st.metric(
                    "Autoevaluación",
                    f"{row['autoevaluacion']}/5",
                )

        if row.get(
            "reflexion_bien"
        ):

            st.success(
                row["reflexion_bien"]
            )

        if row.get(
            "reflexion_mejorar"
        ):

            st.warning(
                row["reflexion_mejorar"]
            )

        st.divider()


# -----------------------------------------------------------------------------
# Paginación
# -----------------------------------------------------------------------------

def _render_pagination(
    page: dict,
    state_key: str,
) -> None:

    cols = st.columns(
        [
            1,
            2,
            2,
            1,
        ]
    )

    current = page["page"]

    total_pages = page["pages"]

    total = page["total"]

    with cols[0]:

        if st.button(
            "◀",
            key=f"{state_key}_prev",
            disabled=current <= 1,
            use_container_width=True,
        ):

            st.session_state[state_key] -= 1

    with cols[1]:

        st.caption(
            f"Página {current} de {total_pages}"
        )

    with cols[2]:

        st.caption(
            f"{total} reflexiones"
        )

    with cols[3]:

        if st.button(
            "▶",
            key=f"{state_key}_next",
            disabled=current >= total_pages,
            use_container_width=True,
        ):

            st.session_state[state_key] += 1


# -----------------------------------------------------------------------------
# Utilidades
# -----------------------------------------------------------------------------

def _format_date(
    value: datetime | str | None,
) -> str:

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