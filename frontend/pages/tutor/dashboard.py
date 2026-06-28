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
    st.session_state.setdefault(
    "selected_panel",
    None,
)




@st.cache_data(
    ttl=300,
    show_spinner=False,
)
def _load_summary() -> dict:
    """
    Carga los KPI del Dashboard.
    """

    return api.get_tutor_summary()

def _load_apprentices(
    page: int,
    size: int,
) -> dict:
    """
    Carga la tabla de aprendices.
    """

    return api.get_tutor_apprentices(
        page=page,
        size=size,
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

        summary = _load_summary()

        page = _load_apprentices(
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
    st.divider()

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "📂 Ver vacantes",
            use_container_width=True,
        ):

            st.session_state["selected_panel"] = "applications"

    with col2:

        if st.button(
            "💭 Ver reflexiones",
            use_container_width=True,
        ):

            st.session_state["selected_panel"] = "reflections"
            
    if st.session_state["selected_panel"] == "applications":

        dashboard_applications.show(
            apprentice["detail"]["id"],
        )

    elif st.session_state["selected_panel"] == "reflections":

        dashboard_reflections.show(
            apprentice["detail"]["id"],
        )


  