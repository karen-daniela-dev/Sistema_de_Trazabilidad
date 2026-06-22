"""
Panel del Aprendiz — Dashboard, aplicaciones y entrevistas.
Formularios completos según especificación.
"""
import streamlit as st
from datetime import datetime, date
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from frontend import api_client as api
from frontend.components.ui import (
    kpi_card, mostrar_semaforo, chart_estados_pie,
    chart_fallas_bar, tabla_aplicaciones, panel_alertas, estado_badge
)

# ── Opciones de formularios según especificación ──────────────────────────────
FALLAS_OPTS = {
    "TECNICA":               "Técnica",
    "COMUNICACION":          "Comunicación",
    "BLANDAS":               "Habilidades blandas",
    "REGULACION_EMOCIONAL":  "Regulación emocional",
}

SUBFALLAS = {
    "TECNICA": [
        "No conocía el tema",
        "Error lógico",
        "Falta de profundidad",
    ],
    "COMUNICACION": [
        "No supe explicar",
        "Falta de claridad",
        "Desorden al hablar",
    ],
    "BLANDAS": [
        "No estructuré respuestas",
        "No comuniqué experiencia",
    ],
    "REGULACION_EMOCIONAL": [
        "Me bloqueé",
        "Perdí el hilo",
        "Nervios altos",
    ],
}

TEMAS_TECNICOS = ["JAVA", "SPRING_BOOT", "APIS", "SQL", "ALGORITMOS", "OTRO"]


def _seccion_perfil():
    """Formulario de perfil para aprendiz sin perfil."""
    st.warning("⚠️ Antes de continuar debes completar tu perfil.")
    st.subheader("📋 Completa tu perfil")

    cohortes = api.get_cohortes()
    tutores = api.get_tutores()

    if not cohortes or not tutores:
        st.error("No hay cohortes o tutores disponibles. Contacta al coordinador.")
        return

    cohortes_activas = [c for c in cohortes if c["estado"] == "ACTIVA"]
    if not cohortes_activas:
        st.error("No hay cohortes activas. Contacta al coordinador.")
        return

    with st.form("form_perfil"):
        st.markdown("**Información de tu programa**")
        cohorte_map = {c["nombre"]: c["id"] for c in cohortes_activas}
        tutor_map = {t["email"]: t["id"] for t in tutores}

        cohorte_sel = st.selectbox("Cohorte *", list(cohorte_map.keys()))
        tutor_sel = st.selectbox("Tutor asignado *", list(tutor_map.keys()))

        st.markdown("**Información de contacto**")
        col1, col2 = st.columns(2)
        with col1:
            telefono = st.text_input("Teléfono")
            ciudad = st.text_input("Ciudad")
        with col2:
            tel_emergencia = st.text_input("Teléfono de emergencia")

        submitted = st.form_submit_button("💾 Guardar perfil", type="primary", use_container_width=True)

    if submitted:
        result = api.crear_perfil({
            "cohorte_id": cohorte_map[cohorte_sel],
            "tutor_id": tutor_map[tutor_sel],
            "telefono": telefono.strip() or None,
            "telefono_emergencia": tel_emergencia.strip() or None,
            "ciudad": ciudad.strip() or None,
        })
        if result:
            st.success("✅ Perfil completado correctamente.")
            st.rerun()


def _tab_dashboard():
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


def _tab_aplicaciones():
    resultado = api.get_aplicaciones()
    if not resultado:
        st.info("No tienes aplicaciones registradas.")
        return

    items = resultado.get("items", [])
    total = resultado.get("total", 0)
    st.caption(f"{total} aplicación(es) registrada(s)")
    tabla_aplicaciones(items)

    if items:
        st.divider()
        app_opts = {
            f"{a['empresa']} — {a['vacante']}": a["id"]
            for a in items if a["estado"] != "CONTRATADO"
        }
        if app_opts:
            st.subheader("✅ Marcar como contratado")
            seleccion = st.selectbox("Selecciona la aplicación:", list(app_opts.keys()))
            if st.button("🎉 Confirmar contratación", type="primary"):
                if api.marcar_contratado(app_opts[seleccion]):
                    st.success("¡Felicitaciones! Estado actualizado a CONTRATADO 🎉")
                    st.rerun()


def _tab_nueva_aplicacion():
    st.subheader("➕ Registrar nueva aplicación")

    with st.form("form_nueva_app", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            empresa = st.text_input("Empresa *", placeholder="Ej: Bancolombia")
            vacante = st.text_input("Vacante / Cargo *", placeholder="Ej: Desarrollador Java Jr")
            link = st.text_input("Link de la oferta", placeholder="https://...")
        with col2:
            modalidad = st.selectbox("Modalidad *", ["REMOTO", "PRESENCIAL", "HIBRIDO"],
                                     format_func=lambda x: {"REMOTO": "🌐 Remoto",
                                                            "PRESENCIAL": "🏢 Presencial",
                                                            "HIBRIDO": "🔄 Híbrido"}[x])
            origen = st.selectbox("Origen de la vacante *",
                                  ["PROPIA", "TUTOR", "EMPLEABILIDAD"],
                                  format_func=lambda x: {"PROPIA": "🔍 Búsqueda propia",
                                                         "TUTOR": "👨‍🏫 Referido por tutor",
                                                         "EMPLEABILIDAD": "🏫 Área de empleabilidad"}[x])
            fecha = st.date_input("Fecha de aplicación *", value=date.today())

        submitted = st.form_submit_button("📤 Registrar aplicación", type="primary", use_container_width=True)

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
                "link": link.strip() or None,
            })
            if result:
                st.success(f"✅ Aplicación a **{empresa}** registrada. Estado inicial: **APLICADO**")
                st.rerun()


def _tab_nueva_entrevista():
    st.subheader("➕ Registrar entrevista")

    resultado = api.get_aplicaciones(size=100)
    apps = resultado.get("items", []) if resultado else []
    apps_disponibles = [a for a in apps if a["estado"] != "CONTRATADO"]

    if not apps_disponibles:
        st.info("Primero registra una aplicación para poder agregar entrevistas.")
        return

    app_map = {
        f"{a['empresa']} — {a['vacante']} [{estado_badge(a['estado'])}]": a["id"]
        for a in apps_disponibles
    }

    with st.form("form_nueva_ent", clear_on_submit=True):
        # ── Sección 1: Información básica ─────────────────────────────────
        st.markdown("**📌 Sección 1: Información básica**")
        app_sel = st.selectbox("Aplicación *", list(app_map.keys()))

        col1, col2 = st.columns(2)
        with col1:
            tipo = st.selectbox("Tipo de entrevista *",
                                ["RRHH", "TECNICA", "PRUEBA_TECNICA"],
                                format_func=lambda x: {"RRHH": "👥 RRHH",
                                                       "TECNICA": "💻 Técnica",
                                                       "PRUEBA_TECNICA": "📝 Prueba técnica"}[x])
            modalidad_e = st.selectbox("Modalidad *",
                                       ["VIRTUAL", "PRESENCIAL"],
                                       format_func=lambda x: {"VIRTUAL": "💻 Virtual",
                                                              "PRESENCIAL": "🏢 Presencial"}[x])
        with col2:
            fecha_e = st.date_input("Fecha *", value=date.today())
            hora_e = st.time_input("Hora *")

        grupal = st.radio("¿Fue grupal?", ["No", "Sí"], horizontal=True) == "Sí"

        # ── Sección 2: Evaluación grupal (condicional) ────────────────────
        percepcion = None
        if grupal:
            st.markdown("**👥 Sección 2: Evaluación grupal**")
            percepcion = st.selectbox(
                "¿Cómo te percibiste frente a los otros candidatos? *",
                ["MEJOR", "IGUAL", "POR_MEJORAR"],
                format_func=lambda x: {"MEJOR": "⭐ Mejor preparado",
                                       "IGUAL": "➡️ Igual que los demás",
                                       "POR_MEJORAR": "📈 Por mejorar"}[x]
            )

        # ── Sección 3: Fallas ─────────────────────────────────────────────
        st.markdown("**⚠️ Sección 3: Fallas identificadas**")
        fallas_sel = st.multiselect(
            "Selecciona las fallas que tuviste (puedes elegir varias):",
            list(FALLAS_OPTS.keys()),
            format_func=lambda x: FALLAS_OPTS[x]
        )

        # ── Sección 4: Subfallas (dinámico) ──────────────────────────────
        subfallas_sel = []
        otra_dificultad = ""
        if fallas_sel:
            st.markdown("**🔍 Sección 4: Detalle de fallas**")
            for falla in fallas_sel:
                opciones = SUBFALLAS.get(falla, [])
                if opciones:
                    sel = st.multiselect(
                        f"Subfallas — {FALLAS_OPTS[falla]}:",
                        opciones,
                        key=f"sub_{falla}"
                    )
                    subfallas_sel.extend(sel)
            otra_dificultad = st.text_input("Otra dificultad (opcional)", placeholder="Describe brevemente...")

        # ── Sección 5: Temas técnicos (condicional) ───────────────────────
        temas = []
        if "TECNICA" in fallas_sel:
            st.markdown("**💻 Sección 5: Temas técnicos con dificultad**")
            temas = st.multiselect("¿En qué temas tuviste dificultad?", TEMAS_TECNICOS)

        # ── Sección 6: Autoevaluación ─────────────────────────────────────
        st.markdown("**⭐ Sección 6: Autoevaluación**")
        autoevaluacion = st.slider("Nivel de preparación general (1 = muy bajo, 5 = excelente)", 1, 5, 3)

        # ── Sección 7: Reflexión ──────────────────────────────────────────
        st.markdown("**💭 Sección 7: Reflexión**")
        bien = st.text_area(
            "¿Qué hiciste bien?",
            placeholder="Ej: expliqué bien un proyecto, respondí con seguridad, llegué puntual..."
        )
        mejorar = st.text_area(
            "¿Qué debes mejorar?",
            placeholder="Ej: estudiar SQL joins, mejorar claridad al hablar, practicar más algoritmos..."
        )

        # ── Sección 8: Respuesta de la empresa (opcional) ─────────────────
        st.markdown("**📬 Sección 8: Respuesta de la empresa** *(opcional)*")
        respuesta = st.selectbox(
            "¿Qué respuesta recibiste?",
            ["", "AVANZO", "RECHAZADO", "SIN_RESPUESTA"],
            format_func=lambda x: {
                "": "— No registrar —",
                "AVANZO": "✅ Avancé en el proceso",
                "RECHAZADO": "❌ Fui rechazado",
                "SIN_RESPUESTA": "⏳ No recibí respuesta"
            }.get(x, x)
        )

        submitted_e = st.form_submit_button("💾 Registrar entrevista", type="primary", use_container_width=True)

    if submitted_e:
        fecha_hora = datetime.combine(fecha_e, hora_e).isoformat()

        # Agregar otra_dificultad a subfallas si fue llenado
        todas_subfallas = subfallas_sel.copy()
        if otra_dificultad.strip():
            todas_subfallas.append(otra_dificultad.strip())

        payload = {
            "aplicacion_id": app_map[app_sel],
            "tipo": tipo,
            "modalidad": modalidad_e,
            "fecha": fecha_hora,
            "grupal": grupal,
            "percepcion_grupal": percepcion if grupal else None,
            "fallas": fallas_sel,
            "subfallas": todas_subfallas,
            "temas_tecnicos": temas,
            "autoevaluacion": autoevaluacion,
            "reflexion_bien": bien.strip() or None,
            "reflexion_mejorar": mejorar.strip() or None,
            "respuesta_empresa": respuesta or None,
        }
        result = api.crear_entrevista(payload)
        if result:
            st.success("✅ Entrevista registrada. El estado de tu aplicación fue actualizado automáticamente.")
            st.rerun()


def show():
    st.title("📊 Mi Panel de Empleabilidad")

    # Verificar perfil
    perfil = api.get_mi_perfil()
    if not perfil:
        _seccion_perfil()
        return

    tab_dashboard, tab_apps, tab_nueva_app, tab_nueva_ent, tab_alertas,tab_perfil = st.tabs([
        "📊 Dashboard",
        "📋 Mis aplicaciones",
        "➕ Nueva aplicación",
        "🗓️ Nueva entrevista",
        "🔔 Alertas",
        "👤 Mi perfil",
    ])

    with tab_dashboard:
        _tab_dashboard()

    with tab_apps:
        _tab_aplicaciones()

    with tab_nueva_app:
        _tab_nueva_aplicacion()

    with tab_nueva_ent:
        _tab_nueva_entrevista()

    with tab_alertas:
        alertas = api.get_alertas()
        panel_alertas(alertas)
        
    with tab_perfil:
        st.subheader("👤 Mi perfil")
        if perfil:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Cohorte:** {perfil.get('cohorte_id', '')}")
                st.markdown(f"**Tutor:** {perfil.get('tutor_id', '')}")
                st.markdown(f"**Ciudad:** {perfil.get('ciudad') or 'No registrada'}")
            with col2:
                st.markdown(f"**Teléfono:** {perfil.get('telefono') or 'No registrado'}")
                st.markdown(f"**Tel. emergencia:** {perfil.get('telefono_emergencia') or 'No registrado'}")

        st.divider()
        st.subheader("✏️ Actualizar datos de contacto")
        with st.form("form_actualizar_perfil"):
            telefono = st.text_input("Teléfono", value=perfil.get("telefono") or "")
            tel_emergencia = st.text_input("Teléfono de emergencia", value=perfil.get("telefono_emergencia") or "")
            ciudad = st.text_input("Ciudad", value=perfil.get("ciudad") or "")
            st.caption("⚠️ No puedes cambiar tu cohorte ni tu tutor.")
            submitted = st.form_submit_button("💾 Guardar cambios", type="primary")

        if submitted:
            result = api.actualizar_perfil({
                "telefono": telefono.strip() or None,
                "telefono_emergencia": tel_emergencia.strip() or None,
                "ciudad": ciudad.strip() or None,
            })
            if result:
                st.success("✅ Perfil actualizado correctamente.")
                st.rerun()