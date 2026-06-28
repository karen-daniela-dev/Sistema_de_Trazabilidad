"""
pages/tutor/dashboard_applications.py

Vacantes del aprendiz seleccionado.
"""

from __future__ import annotations

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
    Muestra las aplicaciones del aprendiz.
    """

    if not aprendiz_id:

        return

    state_key = f"apps_page_{aprendiz_id}"

    if state_key not in st.session_state:

        st.session_state[state_key] = 1

    page = api.get_tutor_applications(
        aprendiz_id=aprendiz_id,
        page=st.session_state[state_key],
        size=PAGE_SIZE,
    )

    if page is None:

        return

    st.subheader(
        "📂 Vacantes"
    )

    rows = page.get(
        "items",
        [],
    )

    if not rows:

        st.info(
            "Este aprendiz aún no registra aplicaciones."
        )

        return

    _render_header()

    for row in rows:

        _render_row(
            row,
        )

    _render_pagination(
        page,
        state_key,
    )


# -----------------------------------------------------------------------------
# Encabezado
# -----------------------------------------------------------------------------

def _render_header() -> None:

    cols = st.columns(
        [
            2.0,
            2.0,
            1.1,
            1.2,
            1.2,
            1.3,
            0.9,
        ]
    )

    cols[0].markdown("**Empresa**")
    cols[1].markdown("**Vacante**")
    cols[2].markdown("**Modalidad**")
    cols[3].markdown("**Origen**")
    cols[4].markdown("**Estado**")
    cols[5].markdown("**Fecha**")
    cols[6].markdown("**Ent.**")

    st.divider()


# -----------------------------------------------------------------------------
# Filas
# -----------------------------------------------------------------------------

def _render_row(
    row: dict,
) -> None:

    cols = st.columns(
        [
            2.0,
            2.0,
            1.1,
            1.2,
            1.2,
            1.3,
            0.9,
        ]
    )

    cols[0].write(
        row["empresa"]
    )

    cols[1].write(
        row["vacante"]
    )

    cols[2].write(
        row["modalidad"]
    )

    cols[3].write(
        row["origen"]
    )

    cols[4].write(
        row["estado"]
    )

    cols[5].write(
        _format_date(
            row["fecha_aplicacion"],
        )
    )

    cols[6].write(
        row["total_entrevistas"]
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
            f"{total} aplicaciones"
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
    value,
) -> str:

    if value is None:

        return "-"

    try:

        from datetime import datetime

        if isinstance(
            value,
            datetime,
        ):

            return value.strftime(
                "%d/%m/%Y",
            )

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