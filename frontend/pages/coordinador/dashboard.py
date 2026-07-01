"""
pages/coordinador/dashboard.py

Dashboard principal del Coordinador.
"""

from __future__ import annotations

import streamlit as st

from frontend import api_client as api

from frontend.pages.tutor import (
    dashboard_detail,
    dashboard_failures,
)




from .dashboard_summary import (
    show as render_summary,
)

from .dashboard_ranking import (
    show as render_ranking,
)

from .dashboard_table import (
    show as render_table,
)

from .dashboard_tutor_detail import (
    show as render_detail,
)
from frontend.components.cohorte_selector import (render as render_cohorte_selector)
from . import dashboard_state

def show():
    dashboard_state.init_state()
    st.title(
        "📊 Dashboard del Coordinador"
    )

    cohorte = render_cohorte_selector()

    if cohorte is None:

        st.info(
            "Seleccione una cohorte."
        )

        return

    cohorte_id = cohorte["id"]

    render_summary(
        cohorte_id,
    )

    st.divider()

    render_ranking(
        cohorte_id,
    )

    st.divider()

    tutor_id = render_table(
        cohorte_id,
    )

    if tutor_id is None:

        return

    st.divider()

    aprendiz_id = render_detail(
        cohorte_id,
        tutor_id,
    )

    if aprendiz_id is None:

        return

    detail = api.get_tutor_apprentice(
        aprendiz_id,
    )

    failures = api.get_tutor_failures(
        aprendiz_id,
    )

    if detail is None:

        return

    st.divider()

    dashboard_detail.show(
        detail,
        compact=True,
    )

    dashboard_failures.show(
        failures,
    )