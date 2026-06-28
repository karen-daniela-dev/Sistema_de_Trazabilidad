"""
pages/tutor/dashboard.py

Dashboard principal del Tutor.
"""

from __future__ import annotations

import streamlit as st

from frontend import api_client as api

from . import dashboard_summary
from . import dashboard_table
from . import dashboard_detail
from . import dashboard_failures
from . import dashboard_applications
from . import dashboard_reflections


PAGE_SIZE = 20


def _init_state() -> None:
    """Inicializa el estado de la página."""

    st.session_state.setdefault(
        "tutor_page",
        1,
    )

    st.session_state.setdefault(
        "selected_apprentice",
        None,
    )


# def _load_dashboard() -> tuple[dict, dict]:
#     """
#     Carga la información principal
#     del Dashboard.
#     """

#     summary = api.get_tutor_summary()

#     page = api.get_tutor_apprentices(
#         page=st.session_state["tutor_page"],
#         size=PAGE_SIZE,
#     )

#     return summary, page
@st.cache_data(
    ttl=60,
    show_spinner=False,
)
def _load_dashboard(
    page: int,
    size: int,
) -> tuple[dict, dict]:
    """
    Carga la información principal
    del Dashboard.
    """

    summary = api.get_tutor_summary()

    apprentices = api.get_tutor_apprentices(
        page=page,
        size=size,
    )

    return (
        summary,
        apprentices,
    )


def _load_selected_apprentice() -> dict | None:
    """
    Carga el detalle del aprendiz
    actualmente seleccionado.
    """

    aprendiz_id = st.session_state.get(
        "selected_apprentice",
    )

    if not aprendiz_id:
        return None

    detail = api.get_tutor_apprentice(
        aprendiz_id,
    )

    if detail is None:
        return None

    failures = api.get_tutor_failures(
        aprendiz_id,
    )

    return {
        "detail": detail,
        "failures": failures,
    }


def show() -> None:

    _init_state()

    st.title(
        "👨‍🏫 Dashboard del Tutor"
    )

    with st.spinner(
        "Cargando dashboard..."
    ):

        summary, page = _load_dashboard(
            page=st.session_state["tutor_page"],
            size=PAGE_SIZE,
        )

    if summary is None or page is None:
        return

    dashboard_summary.show(
        summary,
    )

    dashboard_table.show(
        page,
    )

    apprentice = _load_selected_apprentice()

    if apprentice is None:
        return

    dashboard_detail.show(
        apprentice["detail"],
    )

    dashboard_failures.show(
        apprentice["failures"],
    )
    tab_apps, tab_reflections = st.tabs(
        [
            "📂 Vacantes",
            "💭 Reflexiones",
        ]
    )

    with tab_apps:

        dashboard_applications.show(
            apprentice["detail"]["id"],
        )

    with tab_reflections:

        dashboard_reflections.show(
            apprentice["detail"]["id"],
        )

    dashboard_applications.show()

    dashboard_reflections.show()