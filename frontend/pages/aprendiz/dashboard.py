"""
Panel del Aprendiz — Dashboard, aplicaciones y entrevistas.
"""
import streamlit as st
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from frontend import api_client as api
from frontend.components.ui import (
    kpi_card, mostrar_semaforo, chart_estados_pie,
    chart_fallas_bar, tabla_aplicaciones, panel_alertas, estado_badge
)

FALLAS_OPTS = ["TECNICA", "COMUNICACION", "BLANDAS", "REGULACION_EMOCIONAL"]
SUBFALLAS = {
    "TECNICA": ["JAVA_BASICO", "SPRING_BOOT", "SQL_QUERIES", "ALGORITMOS", "APIS_REST", "ARQUITECTURA"],
    "COMUNICACION": ["CLARIDAD", "ESCUCHA", "ARGUMENTACION"],
    "BLANDAS": ["TRABAJO_EQUIPO", "PUNTUALIDAD", "ACTITUD"],
    "REGULACION_EMOCIONAL": ["ANSIEDAD", "BLOQUEO_MENTAL", "FRUSTACION"],
}


def show():
    st.title("📊 Mi Panel de Empleabilidad")

    tab_dashboard, tab_apps, tab_nueva_app, tab_nueva_ent, tab_alertas = st.tabs([
        "Dashboard", "Mis aplicaciones", "➕ Nueva aplicación",
        "➕ Nueva entrevista", "🔔 Alertas"
    ])

    # ── Dashboard ─────────────────────────────────────────────────────────────
    with tab_dashboard:
        kpis = api.get_kpis_personal()
        if not kpis:
            st.info("Registra tu primera aplicación para ver estadísticas.")
            return

        mostrar_semaforo(kpis.get("semaforo", "GREEN"), "Tu estado actual")
        st.divider()

        c1, c2, c3, c4 = st.columns(4)
        kpi_card(c1, "Aplicaciones", kpis.get("total_aplicaciones", 0))
        kpi_card(c2, "Entrevistas", kpis.get("total_entrevistas", 0))
        kpi_card(c3, "Conversión", f"{kpis.get('tasa_conversion', 0):.0%}")
        contratado = kpis.get("contratado", False)
        kpi_card(c4, "Estado", "🎉 Contratado" if contratado else "En proceso",
                 color="#16a34a" if contratado else "#1a56db")

        st.divider()
        c_left, c_right = st.columns(2)
        with c_left:
            chart_estados_pie(kpis.get("por_estado", {}))
        with c_right:
            chart_fallas_bar(kpis.get("fallas_frecuentes", []))

    # ── Lista de aplicaciones ─────────────────────────────────────────────────
    with tab_apps:
        resultado = api.get_aplicaciones()
        if not resultado:
            st.info("No tienes aplicaciones registradas.")
        else:
            items = resultado.get("items", [])
            total = resultado.get("total", 0)
            st.caption(f"{total} aplicación(es) en total")
            tabla_aplicaciones(items)

            # Acción: marcar contratado
            if items:
                st.divider()
                st.subheader("Acciones")
                app_opts = {f"{a['empresa']} — {a['vacante']}": a["id"] for a in items
                            if a["estado"] != "CONTRATADO"}
                if app_opts:
                    seleccion = st.selectbox("Marcar como CONTRATADO:", list(app_opts.keys()))
                    if st.button("✅ Confirmar contratación", type="primary"):
                        if api.marcar_contratado(app_opts[seleccion]):
                            st.success("¡Felicitaciones! Estado actualizado a CONTRATADO 🎉")
                            st.rerun()

    # ── Nueva aplicación ──────────────────────────────────────────────────────
    with tab_nueva_app:
        st.subheader("Registrar nueva aplicación")
        with st.form("form_nueva_app"):
            empresa = st.text_input("Empresa *")
            vacante = st.text_input("Vacante / Cargo *")
            col1, col2 = st.columns(2)
            with col1:
                modalidad = st.selectbox("Modalidad *", ["REMOTO", "PRESENCIAL", "HIBRIDO"])
                origen = st.selectbox("Origen *", ["PROPIA", "TUTOR", "EMPLEABILIDAD"])
            with col2:
                fecha = st.date_input("Fecha de aplicación *")
            link = st.text_input("Link de la oferta (opcional)")
            submitted = st.form_submit_button("Registrar aplicación", type="primary")

        if submitted:
            if not empresa.strip() or not vacante.strip():
                st.error("Empresa y vacante son obligatorios.")
            else:
                result = api.crear_aplicacion({
                    "empresa": empresa.strip(),
                    "vacante": vacante.strip(),
                    "modalidad": modalidad,
                    "origen": origen,
                    "fecha_aplicacion": str(fecha),
                    "link": link or None,
                })
                if result:
                    st.success(f"✅ Aplicación a {empresa} registrada. Estado: APLICADO")
                    st.rerun()

    # ── Nueva entrevista ──────────────────────────────────────────────────────
    with tab_nueva_ent:
        st.subheader("Registrar entrevista")

        # Cargar aplicaciones disponibles
        resultado = api.get_aplicaciones(size=100)
        apps = resultado.get("items", []) if resultado else []
        apps_no_contratadas = [a for a in apps if a["estado"] != "CONTRATADO"]

        if not apps_no_contratadas:
            st.info("Primero registra una aplicación.")
        else:
            app_map = {f"{a['empresa']} — {a['vacante']} [{estado_badge(a['estado'])}]": a["id"]
                       for a in apps_no_contratadas}

            with st.form("form_nueva_ent"):
                app_sel = st.selectbox("Aplicación *", list(app_map.keys()))
                c1, c2 = st.columns(2)
                with c1:
                    tipo = st.selectbox("Tipo *", ["RRHH", "TECNICA", "PRUEBA_TECNICA"])
                    modalidad_e = st.selectbox("Modalidad *", ["VIRTUAL", "PRESENCIAL"])
                with c2:
                    fecha_e = st.date_input("Fecha *")
                    hora_e = st.time_input("Hora *")

                grupal = st.checkbox("¿Fue grupal?")
                percepcion = None
                if grupal:
                    percepcion = st.selectbox("Percepción grupal *", ["MEJOR", "IGUAL", "POR_MEJORAR"])

                fallas = st.multiselect("Fallas identificadas", FALLAS_OPTS)

                subfallas_sel = []
                if fallas:
                    opciones_sub = []
                    for f in fallas:
                        opciones_sub.extend(SUBFALLAS.get(f, []))
                    subfallas_sel = st.multiselect("Subfallas específicas", list(set(opciones_sub)))

                temas = []
                if "TECNICA" in fallas:
                    temas = st.multiselect("Temas técnicos con dificultad",
                                           ["JAVA", "SPRING_BOOT", "APIS", "SQL", "ALGORITMOS", "OTRO"])

                autoevaluacion = st.slider("Autoevaluación (1-5) *", 1, 5, 3)
                bien = st.text_area("¿Qué hiciste bien?")
                mejorar = st.text_area("¿Qué puedes mejorar?")
                respuesta = st.selectbox("Respuesta de la empresa (opcional)",
                                         ["", "AVANZO", "RECHAZADO", "SIN_RESPUESTA"])

                submitted_e = st.form_submit_button("Registrar entrevista", type="primary")

            if submitted_e:
                fecha_hora = datetime.combine(fecha_e, hora_e).isoformat()
                payload = {
                    "aplicacion_id": app_map[app_sel],
                    "tipo": tipo,
                    "modalidad": modalidad_e,
                    "fecha": fecha_hora,
                    "grupal": grupal,
                    "percepcion_grupal": percepcion if grupal else None,
                    "fallas": fallas,
                    "subfallas": subfallas_sel,
                    "temas_tecnicos": temas,
                    "autoevaluacion": autoevaluacion,
                    "reflexion_bien": bien or None,
                    "reflexion_mejorar": mejorar or None,
                    "respuesta_empresa": respuesta or None,
                }
                result = api.crear_entrevista(payload)
                if result:
                    st.success("✅ Entrevista registrada. Estado de la aplicación actualizado.")
                    st.rerun()

    # ── Alertas ───────────────────────────────────────────────────────────────
    with tab_alertas:
        alertas = api.get_alertas()
        panel_alertas(alertas)
