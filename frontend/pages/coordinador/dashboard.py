"""
Dashboard Coordinador Enterprise

Arquitectura:

Cohorte
    ↓
KPIs
    ↓
Embudo
    ↓
Ranking Tutores
    ↓
Aprendices Tutor
    ↓
Detalle Aprendiz

Toda la información depende
de la cohorte seleccionada.
"""

from __future__ import annotations

import streamlit as st
import pandas as pd

from frontend import api_client as api

from frontend.components.cohorte_selector import (
    render as cohorte_selector,
)

from frontend.components.dashboard_selection_state import (
    get_cohorte,
    get_tutor,
    set_tutor,
    clear_tutor,
)

from frontend.components.ui import (
    kpi_card,
    panel_alertas,
    chart_funnel_global,
    chart_ranking_tutores,
)

# ============================================================
# CACHE
# ============================================================

@st.cache_data(ttl=120)
def load_dashboard_data(cohorte_id: str):

    return {

        "detalle": api.get_kpis_detalle_cohorte(
            cohorte_id
        ),

        "ranking": api.get_kpis_tutores_cohorte(
            cohorte_id
        ),

        "alertas": api.get_alertas(),

    }
    
# ============================================================
# KPIs
# ============================================================

def render_kpis(stats: dict):

    c1, c2, c3, c4 = st.columns(4)

    kpi_card(
        c1,
        "Aprendices",
        stats["total_aprendices"],
    )

    kpi_card(
        c2,
        "Aplicaciones",
        stats["total_aplicaciones"],
    )

    kpi_card(
        c3,
        "Contratados",
        stats["contratados"],
        color="#16a34a",
    )

    kpi_card(
        c4,
        "Tasa",

        f"{stats['tasa_contratacion']:.0%}",

        color="#2563eb",

    )
# ============================================================
# Analytics
# ============================================================

def render_analytics(
    stats: dict,
    aprendices: list,
    alertas: list,
):

    col1, col2 = st.columns([2, 1])

    with col1:

        chart_funnel_global({

            "total_aprendices":
                stats["total_aprendices"],

            "total_aplicaciones":
                stats["total_aplicaciones"],

            "total_entrevistas":

                sum(

                    a["total_entrevistas"]

                    for a in aprendices

                ),

            "contratados_total":
                stats["contratados"],

        })

    with col2:

        panel_alertas(alertas)
# ============================================================
# Ranking Tutores
# ============================================================

def render_ranking(
    ranking,
):

    st.subheader(
        "👨‍🏫 Tutores"
    )

    chart_ranking_tutores(
        ranking
    )

    st.caption(
        "Seleccione un tutor para ver únicamente sus aprendices."
    )

# ============================================================
# Tutor Selector
# ============================================================

def render_tutores(ranking):

    if not ranking:

        st.info(
            "No existen tutores asignados a esta cohorte."
        )

        clear_tutor()

        return None

    nombres = [

        f"{t['email']}  ({t['total_aprendices']} aprendices)"

        for t in ranking

    ]

    actual = get_tutor()

    default = 0

    if actual:

        for i, tutor in enumerate(ranking):

            if tutor["tutor_id"] == actual["tutor_id"]:

                default = i

                break

    indice = st.selectbox(

        "Tutor",

        options=range(len(ranking)),

        index=default,

        format_func=lambda x: nombres[x],

    )

    seleccionado = ranking[indice]

    set_tutor(seleccionado)

    return seleccionado

# ============================================================
# Aprendices
# ============================================================

def render_aprendices(aprendices):

    if not aprendices:

        st.info(
            "Este tutor no tiene aprendices."
        )

        return

    filas = []

    for a in aprendices:

        filas.append(

            {

                "Aprendiz":
                    a["email"],

                "Apps":
                    a["apps"],

                "Entrevistas":
                    a["entrevistas"],

                "Contratado":

                    "✅"

                    if a["contratado"]

                    else "",

                "Actividad":
                    a["actividad"],

                "Progreso":
                    a["progreso"],

            }

        )

    st.dataframe(

        pd.DataFrame(filas),

        use_container_width=True,

        hide_index=True,

    )

# ============================================================
# Tutor Dashboard
# ============================================================

def render_tutor_dashboard(cohorte_id):

    tutor = get_tutor()

    if tutor is None:

        return

    with st.spinner(

        "Cargando tutor..."

    ):

        detalle = api.get_kpi_tutor_cohorte(

            cohorte_id,

            tutor["tutor_id"],

        )

    if not detalle:

        return

    st.divider()

    st.subheader(

        f"👨‍🏫 {detalle['tutor']['email']}"

    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(

        "Aprendices",

        detalle["stats"]["aprendices"],

    )

    c2.metric(

        "Aplicaciones",

        detalle["stats"]["apps"],

    )

    c3.metric(

        "Entrevistas",

        detalle["stats"]["entrevistas"],

    )

    c4.metric(

        "Contratados",

        detalle["stats"]["contratados"],

    )

    render_aprendices(
    detalle["aprendices"]
    )

    render_selector_aprendiz(
        detalle["aprendices"]
    )

    render_aprendiz_dashboard()
    
# ============================================================
# Dashboard
# ============================================================

def show():

    st.title("🏢 Dashboard Coordinador")

    st.caption(
        "Centro de Control de Cohortes"
    )

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
    # Dashboard
    ####################################################################

    with st.spinner(
        "Construyendo dashboard..."
    ):

        dashboard = load_dashboard_data(

            str(cohorte["id"])

        )

    if dashboard is None:

        st.error(
            "No fue posible cargar el dashboard."
        )

        return

    detalle = dashboard["detalle"]

    ranking = dashboard["ranking"]

    alertas = dashboard["alertas"]

    if not detalle:

        st.warning(
            "La cohorte seleccionada aún no posee información."
        )

        return

    stats = detalle["stats"]

    aprendices = detalle["aprendices"]

    ####################################################################
    # Header Cohorte
    ####################################################################

    with st.container(border=True):

        c1, c2, c3 = st.columns([2,1,1])

        with c1:

            st.subheader(
                cohorte["nombre"]
            )

            st.caption(
                f"Estado: {cohorte['estado']}"
            )

        with c2:

            st.metric(
                "Meta",
                cohorte["meta_contratacion"]
            )

        with c3:

            st.metric(
                "Finaliza",
                cohorte["fecha_fin"]
            )

    st.divider()

    ####################################################################
    # KPIs
    ####################################################################

    render_kpis(
        stats
    )

    st.divider()

    ####################################################################
    # Analytics
    ####################################################################

    render_analytics(

        stats,

        aprendices,

        alertas,

    )

    st.divider()

    ####################################################################
    # Tutores
    ####################################################################

    render_ranking(
        ranking
    )

    tutor = render_tutores(
        ranking
    )

    ####################################################################
    # Drill Down Tutor
    ####################################################################

    if tutor:

        render_tutor_dashboard(

            str(
                cohorte["id"]
            )

        )
# ============================================================
# Aprendiz Selector
# ============================================================

from frontend.components.dashboard_selection_state import (
    get_aprendiz,
    set_aprendiz,
)


def render_selector_aprendiz(aprendices):

    if not aprendices:
        return None

    actual = get_aprendiz()

    default = 0

    if actual:

        for i, a in enumerate(aprendices):

            if a["usuario_id"] == actual["usuario_id"]:

                default = i

                break

    indice = st.selectbox(

        "Aprendiz",

        options=range(len(aprendices)),

        index=default,

        format_func=lambda x:
            aprendices[x]["email"],

    )

    seleccionado = aprendices[indice]

    set_aprendiz(seleccionado)

    return seleccionado

# ============================================================
# Dashboard Aprendiz
# ============================================================

def render_aprendiz_dashboard():

    aprendiz = get_aprendiz()

    if aprendiz is None:

        return

    with st.spinner(
        "Cargando aprendiz..."
    ):

        detalle = api.get_kpi_aprendiz(

            aprendiz["usuario_id"]

        )

    if not detalle:

        return

    st.divider()

    st.subheader(
        f"🎓 {detalle['perfil']['email']}"
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Aplicaciones",
        detalle["kpis"]["total_aplicaciones"]
    )

    c2.metric(
        "Entrevistas",
        detalle["kpis"]["total_entrevistas"]
    )

    c3.metric(
        "Contratado",
        "Sí" if detalle["kpis"]["contratado"] else "No"
    )

    c4.metric(
        "Semáforo",
        detalle["kpis"]["progreso"]
    )

    tab1, tab2, tab3, tab4 = st.tabs(

        [

            "📄 Aplicaciones",

            "🎤 Entrevistas",

            "🚨 Alertas",

            "📈 Analítica",

        ]

    )

    with tab1:

        st.dataframe(

            detalle["aplicaciones"],

            use_container_width=True,

            hide_index=True,

        )

    with tab2:

        st.dataframe(

            detalle["entrevistas"],

            use_container_width=True,

            hide_index=True,

        )

    with tab3:

        if detalle["alertas"]:

            panel_alertas(

                detalle["alertas"]

            )

        else:

            st.success(
                "Sin alertas."
            )

    with tab4:

        c1, c2 = st.columns(2)

        with c1:

            st.metric(

                "Tasa Conversión",

                f"{detalle['kpis']['conversion']:.0%}"

            )

        with c2:

            st.metric(

                "Rechazos",

                detalle["kpis"]["rechazos"]

            )
