"""
Panel del Tutor — Vista de grupo, alertas y análisis de aprendices.
"""
import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from frontend import api_client as api
from frontend.components.ui import (
    kpi_card, mostrar_semaforo, chart_semaforos_grupo,
    chart_fallas_bar, panel_alertas
)

SEMAFORO_EMOJI = {"GREEN": "🟢", "YELLOW": "🟡", "RED": "🔴"}


def show():
    st.title("👨‍🏫 Panel del Tutor")

    tab_grupo, tab_alertas = st.tabs(["Mi grupo", "🔔 Alertas"])

    with tab_grupo:
        with st.spinner("Cargando datos del grupo..."):
            kpis = api.get_kpis_grupo()

        if not kpis:
            st.info("No tienes aprendices asignados aún.")
            return

        resumen = kpis.get("resumen", {})
        total = kpis.get("total_aprendices", 0)

        # KPIs del grupo
        c1, c2, c3, c4 = st.columns(4)
        kpi_card(c1, "Aprendices", total)
        kpi_card(c2, "Contratados", resumen.get("contratados", 0), color="#16a34a")
        kpi_card(c3, "En riesgo 🟡", resumen.get("YELLOW", 0), color="#ca8a04")
        kpi_card(c4, "Críticos 🔴", resumen.get("RED", 0), color="#dc2626")

        st.divider()
        chart_semaforos_grupo(resumen)
        st.divider()

        # Tabla detallada por aprendiz
        st.subheader("Detalle por aprendiz")
        aprendices = kpis.get("aprendices", [])

        if aprendices:
            filas = []
            for a in aprendices:
                sem = a.get("semaforo", "GREEN")
                filas.append({
                    "Estado": f"{SEMAFORO_EMOJI.get(sem, '⚪')} {sem}",
                    "Email": a.get("email", ""),
                    "Aplicaciones": a.get("total_aplicaciones", 0),
                    "Entrevistas": a.get("total_entrevistas", 0),
                    "Conversión": f"{a.get('tasa_conversion', 0):.0%}",
                    "Contratado": "🎉 Sí" if a.get("contratado") else "No",
                })
            df = pd.DataFrame(filas)
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Drill-down por aprendiz
            st.divider()
            emails = [a["email"] for a in aprendices]
            email_sel = st.selectbox("Ver detalle de:", emails)
            aprendiz_data = next((a for a in aprendices if a["email"] == email_sel), None)

            if aprendiz_data:
                col1, col2 = st.columns(2)
                with col1:
                    mostrar_semaforo(aprendiz_data.get("semaforo", "GREEN"), "Semáforo")
                    st.metric("Aplicaciones", aprendiz_data.get("total_aplicaciones", 0))
                    st.metric("Entrevistas", aprendiz_data.get("total_entrevistas", 0))
                with col2:
                    chart_fallas_bar(aprendiz_data.get("fallas_frecuentes", []))

                por_estado = aprendiz_data.get("por_estado", {})
                if any(por_estado.values()):
                    st.subheader("Estados de sus aplicaciones")
                    for estado, n in por_estado.items():
                        if n > 0:
                            st.write(f"• **{estado}**: {n}")

    with tab_alertas:
        alertas = api.get_alertas()
        panel_alertas(alertas)
        if alertas:
            if st.button("Marcar todas como leídas"):
                for a in alertas:
                    api.marcar_alerta_leida(a["id"])
                st.rerun()
