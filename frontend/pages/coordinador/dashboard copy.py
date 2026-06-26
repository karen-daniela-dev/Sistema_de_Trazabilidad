"""
Dashboard Coordinador

Arquitectura Enterprise

Flujo:

Cohorte
    ↓
KPIs
    ↓
Embudo
    ↓
Ranking Tutores
    ↓
Alertas

No existen KPIs globales.
Todo depende de la cohorte seleccionada.
"""

import streamlit as st

from frontend import api_client as api

from frontend.components.cohorte_selector import render as cohorte_selector

from frontend.components.dashboard_state_coor import (
    get_cohorte,
)

from frontend.components.ui import (
    kpi_card,
    panel_alertas,
    chart_funnel_global,
    chart_ranking_tutores,
)


# =====================================================================
# Helpers
# =====================================================================

def _load_dashboard():

    cohorte = get_cohorte()

    if cohorte is None:
        return None

    cohorte_id = str(cohorte["id"])

    return {

        "detalle": api.get_kpis_detalle_cohorte(
            cohorte_id
        ),

        "ranking": api.get_kpis_tutores(),

        "alertas": api.get_alertas(),
    }


# =====================================================================
# Dashboard
# =====================================================================

def show():

    st.title("🏢 Dashboard Coordinador")

    st.divider()

    ####################################################################
    # Contexto
    ####################################################################

    cohorte_selector()

    cohorte = get_cohorte()

    if cohorte is None:

        st.info(
            "Seleccione una cohorte."
        )

        return

    ####################################################################
    # Datos
    ####################################################################

    with st.spinner(
        "Cargando Dashboard..."
    ):

        dashboard = _load_dashboard()

    if dashboard is None:

        st.error(
            "No fue posible cargar la información."
        )

        return

    detalle = dashboard["detalle"]

    ranking = dashboard["ranking"]

    alertas = dashboard["alertas"]

    if not detalle:

        st.warning(
            "La cohorte no tiene información."
        )

        return

    stats = detalle["stats"]

    ####################################################################
    # KPIs
    ####################################################################

    st.subheader("Resumen Ejecutivo")

    c1, c2, c3, c4 = st.columns(4)

    kpi_card(
        c1,
        "Aprendices",
        stats["total_aprendices"]
    )

    kpi_card(
        c2,
        "Aplicaciones",
        stats["total_aplicaciones"]
    )

    kpi_card(
        c3,
        "Contratados",
        stats["contratados"],
        color="#16a34a"
    )

    kpi_card(
        c4,
        "Tasa",

        f"{stats['tasa_contratacion']:.0%}",

        color="#1a56db"
    )

    st.divider()

    ####################################################################
    # Analytics
    ####################################################################

    col1, col2 = st.columns(
        [2, 1]
    )

    with col1:

        chart_funnel_global({

            "total_aprendices":
                stats["total_aprendices"],

            "total_aplicaciones":
                stats["total_aplicaciones"],

            "total_entrevistas":
                sum(

                    a["total_entrevistas"]

                    for a in detalle["aprendices"]

                ),

            "contratados_total":
                stats["contratados"],

        })

    with col2:

        panel_alertas(alertas)

    st.divider()

    ####################################################################
    # Tutores
    ####################################################################

    st.subheader(
        "Ranking de Tutores"
    )

    chart_ranking_tutores(
        ranking
    )

    st.divider()

    ####################################################################
    # Aprendices
    ####################################################################

    st.subheader(
        "Aprendices"
    )

    rows = []

    for a in detalle["aprendices"]:

        rows.append({

            "Aprendiz":
                a["email"],

            "Tutor":
                a["tutor_email"],

            "Apps":
                a["total_aplicaciones"],

            "Entrevistas":
                a["total_entrevistas"],

            "Contratado":

                "✅"

                if a["contratado"]

                else "",

            "Actividad":
                a["semaforo_actividad"],

            "Progreso":
                a["semaforo_progreso"],

        })

    st.dataframe(

        rows,

        use_container_width=True,

        hide_index=True,

    )

    st.divider()

    ####################################################################
    # Futuro
    ####################################################################

    st.caption(
        "Próxima versión: Drill-down Tutor → Aprendiz"
    )