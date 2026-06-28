"""
pages/tutor/dashboard_table.py

Tabla principal del Dashboard del Tutor.
"""

from __future__ import annotations

from datetime import datetime

import streamlit as st


# -----------------------------------------------------------------------------
# Tabla principal
# -----------------------------------------------------------------------------

def show(
    page: dict,
) -> None:
    """
    Renderiza la tabla principal de aprendices.
    """

    rows = page.get(
        "items",
        [],
    )

    if not rows:

        st.info(
            "No existen aprendices asignados."
        )

        return

    _render_header()

    for row in rows:

        _render_row(
            row,
        )

    _render_pagination(
        page,
    )


# -----------------------------------------------------------------------------
# Encabezado
# -----------------------------------------------------------------------------

def _render_header() -> None:
    """
    Renderiza el encabezado de la tabla.
    """

    cols = st.columns(
        [
            2.8,   # Aprendiz
            1.3,   # Teléfono
            1.3,   # Emergencia
            0.8,   # Apps
            0.8,   # Actividad
            0.8,   # Progreso
            0.9,   # Contratado
            1.5,   # Última actividad
            0.9,   # Acción
        ]
    )

    cols[0].markdown("**Aprendiz**")
    cols[1].markdown("**Teléfono**")
    cols[2].markdown("**Emergencia**")
    cols[3].markdown("**Apps**")
    cols[4].markdown("**Actividad**")
    cols[5].markdown("**Progreso**")
    cols[6].markdown("**✔**")
    cols[7].markdown("**Última actividad**")
    cols[8].markdown("**Acción**")

    st.divider()
    
# -----------------------------------------------------------------------------
# Filas
# -----------------------------------------------------------------------------

def _render_row(
    row: dict,
) -> None:
    """
    Renderiza una fila de la tabla.
    """

    cols = st.columns(
        [
            2.8,  # Aprendiz
            1.3,  # Teléfono
            1.3,  # Emergencia
            0.8,  # Apps
            0.8,  # Actividad
            0.8,  # Progreso
            0.9,  # Contratado
            1.5,  # Última actividad
            0.9,  # Acción
        ]
    )

    # Aprendiz

    cols[0].markdown(
        f"**{row['nombre']}**"
    )

    cols[0].caption(
        row["email"]
    )

    # Teléfono

    cols[1].markdown(
        row.get("telefono") or "-"
    )

    # Emergencia

    cols[2].markdown(
        row.get("telefono_emergencia") or "-"
    )

    # Aplicaciones

    cols[3].markdown(
        str(
            row["total_aplicaciones"],
        )
    )

    # Actividad

    cols[4].markdown(
        _semaphore_icon(
            row["actividad"],
        )
    )

    # Progreso

    cols[5].markdown(
        _semaphore_icon(
            row["progreso"],
        )
    )

    # Contratado

    cols[6].markdown(
        "✅"
        if row["contratado"]
        else "—"
    )

    # Última actividad

    cols[7].markdown(
        _format_date(
            row.get(
                "ultima_actividad",
            )
        )
    )

    # Acción

    if cols[8].button(
        "Ver",
        key=f"detail_{row['id']}",
        use_container_width=True,
    ):

        st.session_state[
            "selected_apprentice"
        ] = row["id"]

    st.divider()


# -----------------------------------------------------------------------------
# Utilidades
# -----------------------------------------------------------------------------

def _semaphore_icon(
    estado: str,
) -> str:
    """
    Convierte el estado del semáforo
    en un indicador visual.
    """

    icons = {
        "GREEN": "🟢",
        "YELLOW": "🟡",
        "RED": "🔴",
        "INSUFFICIENT_DATA": "⚪",
    }

    return icons.get(
        estado,
        "⚪",
    )


def _format_date(
    value: datetime | str | None,
) -> str:
    """
    Formatea fechas para la tabla.
    """

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
    
# -----------------------------------------------------------------------------
# Paginación
# -----------------------------------------------------------------------------

def _render_pagination(
    page: dict,
) -> None:
    """
    Renderiza los controles
    de paginación.
    """

    st.divider()

    cols = st.columns(
        [
            1,
            2,
            2,
            1,
        ]
    )

    current_page = page.get(
        "page",
        1,
    )

    total_pages = page.get(
        "pages",
        1,
    )

    total_rows = page.get(
        "total",
        0,
    )

    with cols[0]:

        if st.button(
            "◀",
            disabled=current_page <= 1,
            use_container_width=True,
            key="tutor_prev_page",
        ):

            st.session_state[
                "tutor_page"
            ] = current_page - 1

    with cols[1]:

        st.caption(
            f"Página {current_page} de {total_pages}"
        )

    with cols[2]:

        st.caption(
            f"{total_rows} aprendices"
        )

    with cols[3]:

        if st.button(
            "▶",
            disabled=current_page >= total_pages,
            use_container_width=True,
            key="tutor_next_page",
        ):

            st.session_state[
                "tutor_page"
            ] = current_page + 1