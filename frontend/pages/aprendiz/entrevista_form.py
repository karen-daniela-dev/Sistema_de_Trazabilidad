"""
Formulario de entrevista separado — sin st.form para permitir
campos condicionales dinámicos reactivos.
"""
import streamlit as st
from datetime import datetime, date
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from frontend import api_client as api
from frontend.components.ui import estado_badge

FALLAS_OPTS = {
    "TECNICA":              "💻 Técnica",
    "COMUNICACION":         "🗣️ Comunicación",
    "BLANDAS":              "🤝 Habilidades blandas",
    "REGULACION_EMOCIONAL": "🧘 Regulación emocional",
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


def show_form(apps_disponibles: list):
    if not apps_disponibles:
        st.info("Primero registra una aplicación para poder agregar entrevistas.")
        return

    app_map = {
        f"{a['empresa']} — {a['vacante']} [{estado_badge(a['estado'])}]": a["id"]
        for a in apps_disponibles
    }

    # ── Sección 1: Información básica ─────────────────────────────────────────
    st.markdown("### 📌 Sección 1: Información básica")
    app_sel = st.selectbox("Aplicación *", list(app_map.keys()), key="ent_app")

    col1, col2 = st.columns(2)
    with col1:
        tipo = st.selectbox("Tipo de entrevista *",
                            ["RRHH", "TECNICA", "PRUEBA_TECNICA"],
                            format_func=lambda x: {
                                "RRHH": "👥 RRHH",
                                "TECNICA": "💻 Técnica",
                                "PRUEBA_TECNICA": "📝 Prueba técnica"
                            }[x], key="ent_tipo")
        modalidad_e = st.selectbox("Modalidad *",
                                   ["VIRTUAL", "PRESENCIAL"],
                                   format_func=lambda x: {
                                       "VIRTUAL": "💻 Virtual",
                                       "PRESENCIAL": "🏢 Presencial"
                                   }[x], key="ent_modalidad")
    with col2:
        fecha_e = st.date_input("Fecha *", value=date.today(), key="ent_fecha")
        hora_e = st.time_input("Hora *", key="ent_hora")

    grupal = st.radio("¿Fue grupal?", ["No", "Sí"],
                      horizontal=True, key="ent_grupal") == "Sí"

    # ── Sección 2: Evaluación grupal (condicional) ────────────────────────────
    percepcion = None
    if grupal:
        st.markdown("### 👥 Sección 2: Evaluación grupal")
        percepcion = st.selectbox(
            "¿Cómo te percibiste frente a los otros candidatos? *",
            ["MEJOR", "IGUAL", "POR_MEJORAR"],
            format_func=lambda x: {
                "MEJOR": "⭐ Mejor preparado",
                "IGUAL": "➡️ Igual que los demás",
                "POR_MEJORAR": "📈 Por mejorar"
            }[x], key="ent_percepcion"
        )

    # ── Sección 3: Fallas ─────────────────────────────────────────────────────
    st.markdown("### ⚠️ Sección 3: Fallas identificadas")
    fallas_sel = st.multiselect(
        "Selecciona las fallas que tuviste (puedes elegir varias):",
        list(FALLAS_OPTS.keys()),
        format_func=lambda x: FALLAS_OPTS[x],
        key="ent_fallas"
    )

    # ── Sección 4: Subfallas dinámicas ────────────────────────────────────────
    subfallas_sel = []
    otra_dificultad = ""
    if fallas_sel:
        st.markdown("### 🔍 Sección 4: Detalle de fallas")
        for falla in fallas_sel:
            opciones = SUBFALLAS.get(falla, [])
            if opciones:
                sel = st.multiselect(
                    f"Subfallas — {FALLAS_OPTS[falla]}:",
                    opciones,
                    key=f"ent_sub_{falla}"
                )
                subfallas_sel.extend(sel)
        otra_dificultad = st.text_input(
            "Otra dificultad (opcional)",
            placeholder="Describe brevemente...",
            key="ent_otra"
        )

    # ── Sección 5: Temas técnicos (condicional) ───────────────────────────────
    temas = []
    if "TECNICA" in fallas_sel:
        st.markdown("### 💻 Sección 5: Temas técnicos con dificultad")
        temas = st.multiselect(
            "¿En qué temas tuviste dificultad?",
            TEMAS_TECNICOS,
            key="ent_temas"
        )

    # ── Sección 6: Autoevaluación ─────────────────────────────────────────────
    st.markdown("### ⭐ Sección 6: Autoevaluación")
    autoevaluacion = st.slider(
        "Nivel de preparación general (1 = muy bajo, 5 = excelente)",
        1, 5, 3, key="ent_auto"
    )

    # ── Sección 7: Reflexión ──────────────────────────────────────────────────
    st.markdown("### 💭 Sección 7: Reflexión")
    bien = st.text_area(
        "¿Qué hiciste bien?",
        placeholder="Ej: expliqué bien un proyecto, respondí con seguridad, llegué puntual...",
        key="ent_bien"
    )
    mejorar = st.text_area(
        "¿Qué debes mejorar?",
        placeholder="Ej: estudiar SQL joins, mejorar claridad al hablar, practicar más algoritmos...",
        key="ent_mejorar"
    )

    # ── Sección 8: Respuesta empresa (opcional) ───────────────────────────────
    st.markdown("### 📬 Sección 8: Respuesta de la empresa *(opcional)*")
    respuesta = st.selectbox(
        "¿Qué respuesta recibiste?",
        ["", "AVANZO", "RECHAZADO", "SIN_RESPUESTA"],
        format_func=lambda x: {
            "": "— No registrar —",
            "AVANZO": "✅ Avancé en el proceso",
            "RECHAZADO": "❌ Fui rechazado",
            "SIN_RESPUESTA": "⏳ No recibí respuesta"
        }.get(x, x),
        key="ent_respuesta"
    )

    st.divider()
    if st.button("💾 Registrar entrevista", type="primary", use_container_width=True, key="ent_submit"):
        # Validaciones
        if grupal and not percepcion:
            st.error("Debes seleccionar la percepción grupal.")
            return

        fecha_hora = datetime.combine(fecha_e, hora_e).isoformat()
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
            st.success("✅ Entrevista registrada. Estado de tu aplicación actualizado automáticamente.")
            # Limpiar estado del formulario
            for key in list(st.session_state.keys()):
                if key.startswith("ent_"):
                    del st.session_state[key]
            st.rerun()