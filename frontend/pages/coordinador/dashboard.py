"""
Panel del Coordinador — KPIs globales, cohortes y tutores.
"""
import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from frontend import api_client as api
from frontend.components.ui import (
    kpi_card, chart_cohortes_barras, panel_alertas, mostrar_semaforo
)

SEMAFORO_EMOJI = {"GREEN": "🟢", "YELLOW": "🟡", "RED": "🔴"}


def show():
    st.title("🏢 Panel del Coordinador")

    tab_global, tab_cohortes, tab_tutores, tab_gestionar, tab_alertas = st.tabs([
        "KPIs globales", "Cohortes", "Tutores", "⚙️ Gestionar", "🔔 Alertas"
    ])

    # ── KPIs Globales ─────────────────────────────────────────────────────────
    with tab_global:
        with st.spinner("Cargando datos globales..."):
            kpis = api.get_kpis_globales()

        if not kpis:
            return

        c1, c2, c3, c4 = st.columns(4)
        kpi_card(c1, "Total aprendices", kpis.get("total_aprendices", 0))
        kpi_card(c2, "Aplicaciones", kpis.get("total_aplicaciones", 0))
        kpi_card(c3, "Entrevistas", kpis.get("total_entrevistas", 0))
        tasa = kpis.get("tasa_contratacion_global", 0)
        kpi_card(c4, "Tasa contratación", f"{tasa:.1%}", color="#16a34a")

        st.divider()
        chart_cohortes_barras(kpis.get("cohortes", []))

    # ── Cohortes ──────────────────────────────────────────────────────────────
    with tab_cohortes:
        cohortes = api.get_cohortes()
        if cohortes:
            filas = []
            for c in cohortes:
                sem = SEMAFORO_EMOJI.get(c.get("semaforo", "GREEN"), "⚪")
                filas.append({
                    "Semáforo": sem,
                    "Nombre": c["nombre"],
                    "Estado": c["estado"],
                    "Inicio": c["fecha_inicio"],
                    "Fin": c["fecha_fin"],
                    "Meta": c["meta_contratacion"],
                    "Contratados": c.get("contratados", 0),
                    "% Meta": f"{c.get('pct_meta', 0):.0%}",
                    "Aprendices": c.get("total_aprendices", 0),
                })
            st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("Crear nueva cohorte")
        with st.form("form_cohorte"):
            nombre = st.text_input("Nombre de la cohorte *")
            col1, col2 = st.columns(2)
            with col1:
                fecha_inicio = st.date_input("Fecha de inicio *")
                meta = st.number_input("Meta de contratación *", min_value=1, value=10)
            with col2:
                extension = st.checkbox("Permitir extensión al finalizar")
            submit_c = st.form_submit_button("Crear cohorte", type="primary")

        if submit_c:
            if not nombre.strip():
                st.error("El nombre es obligatorio.")
            else:
                result = api.crear_cohorte({
                    "nombre": nombre.strip(),
                    "fecha_inicio": str(fecha_inicio),
                    "meta_contratacion": meta,
                    "permitir_extension": extension,
                })
                if result:
                    st.success(f"✅ Cohorte '{nombre}' creada. Finaliza: {result['fecha_fin']}")
                    st.rerun()

    # ── Tutores ───────────────────────────────────────────────────────────────
    with tab_tutores:
        kpis = api.get_kpis_globales()
        ranking = kpis.get("ranking_tutores", []) if kpis else []

        if ranking:
            st.subheader("🏆 Ranking de tutores")
            filas = []
            for i, t in enumerate(ranking, 1):
                filas.append({
                    "Posición": f"#{i}",
                    "Email": t["email"],
                    "Aprendices": t["total_aprendices"],
                    "Contratados": t["contratados"],
                    "En verde 🟢": t["semaforo_verde"],
                })
            st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("Registrar nuevo tutor")
        with st.form("form_tutor"):
            email_t = st.text_input("Email del tutor *")
            submit_t = st.form_submit_button("Crear tutor y enviar activación", type="primary")

        if submit_t:
            if not email_t.strip():
                st.error("El email es obligatorio.")
            else:
                result = api.crear_tutor(email_t.strip())
                if result:
                    st.success(f"✅ Tutor creado. Email de activación enviado a {email_t}")

    # ── Gestionar ─────────────────────────────────────────────────────────────
    with tab_gestionar:
        st.subheader("⚙️ Herramientas de administración")
        if st.button("🔄 Sincronizar estados de cohortes"):
            import requests
            token = st.session_state.get("token", "")
            r = requests.post(
                f"{os.getenv('API_BASE_URL', 'http://localhost:8000')}/cohortes/sincronizar-estados",
                headers={"Authorization": f"Bearer {token}"},
            )
            if r.ok:
                n = r.json().get("cohortes_actualizadas", 0)
                st.success(f"✅ {n} cohorte(s) actualizada(s).")
            else:
                st.error("Error al sincronizar.")

    # ── Alertas ───────────────────────────────────────────────────────────────
    with tab_alertas:
        alertas = api.get_alertas()
        panel_alertas(alertas)
