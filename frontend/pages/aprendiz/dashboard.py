"""
Panel del Aprendiz — Dashboard completo con visualizaciones dinámicas Plotly.
"""
import streamlit as st
from datetime import datetime, date, timedelta
import sys, os
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from frontend import api_client as api
from frontend.components.ui import (
    kpi_card, mostrar_semaforo, panel_alertas, estado_badge
)
from frontend.pages.aprendiz.entrevista_form import show_form as entrevista_form
from frontend.pages.aprendiz.fallas_tab import show as fallas_show

# ── Paleta ────────────────────────────────────────────────────────────────────
ESTADO_COLOR = {
    "APLICADO":   "#94a3b8",
    "EN_ESPERA":  "#3b82f6",
    "AVANZANDO":  "#8b5cf6",
    "RECHAZADO":  "#ef4444",
    "CONTRATADO": "#22c55e",
}
FALLAS_LABEL = {
    "TECNICA":              "Técnica",
    "COMUNICACION":         "Comunicación",
    "BLANDAS":              "Habilidades blandas",
    "REGULACION_EMOCIONAL": "Regulación emocional",
    "SIN_FALLAS":           "Sin fallas",
}
SEMAFORO_COLOR = {"GREEN": "#22c55e", "YELLOW": "#f59e0b", "RED": "#ef4444"}
SEMAFORO_LABEL = {"GREEN": "🟢 Al día", "YELLOW": "🟡 Requiere atención", "RED": "🔴 Crítico"}


# ── Helpers de datos ──────────────────────────────────────────────────────────

def _cargar_datos():
    """Carga y estructura todos los datos del aprendiz en un solo bloque."""
    kpis      = api.get_kpis_personal() or {}
    resultado = api.get_aplicaciones(size=100) or {}
    apps      = resultado.get("items", [])

    entrevistas_por_app = {}
    for a in apps:
        ents = api.get_entrevistas(a["id"]) or []
        entrevistas_por_app[a["id"]] = ents

    return kpis, apps, entrevistas_por_app


# ── Bloque 1: Semáforo + métricas ─────────────────────────────────────────────

def _bloque_semaforo(kpis, apps, entrevistas_por_app):
    semaforo = kpis.get("semaforo", "GREEN")
    color    = SEMAFORO_COLOR[semaforo]
    label    = SEMAFORO_LABEL[semaforo]

    total_ents = sum(len(v) for v in entrevistas_por_app.values())
    todas_ents = [e for v in entrevistas_por_app.values() for e in v]
    autoevals  = [e["autoevaluacion"] for e in todas_ents if e.get("autoevaluacion")]
    prom_auto  = round(sum(autoevals) / len(autoevals), 1) if autoevals else 0

    # Semáforo grande
    st.markdown(
        f"""<div style="background:{color}18;border:2px solid {color};border-radius:12px;
        padding:18px 24px;margin-bottom:16px;display:flex;align-items:center;gap:16px">
        <span style="font-size:2.5rem">{"🟢" if semaforo=="GREEN" else "🟡" if semaforo=="YELLOW" else "🔴"}</span>
        <div>
            <p style="margin:0;font-size:1.1rem;font-weight:700;color:{color}">{label}</p>
            <p style="margin:0;font-size:.85rem;color:#64748b">Estado de tu proceso de empleabilidad</p>
        </div>
        </div>""",
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    kpi_card(c1, "Aplicaciones", len(apps), "empresas contactadas")
    kpi_card(c2, "Entrevistas", total_ents, "realizadas en total")
    kpi_card(c3, "Autoevaluación promedio",
             f"{prom_auto}/5" if prom_auto else "—",
             "basado en tus registros",
             color="#8b5cf6")


# ── Bloque 2: Vacantes y etapas ───────────────────────────────────────────────

def _bloque_vacantes(apps, entrevistas_por_app):
    st.markdown("### 📂 Mis vacantes y su progreso")

    if not apps:
        st.info("Aún no tienes aplicaciones registradas.")
        return

    for app in apps:
        estado  = app["estado"]
        color   = ESTADO_COLOR.get(estado, "#94a3b8")
        ents    = entrevistas_por_app.get(app["id"], [])
        n_ents  = len(ents)

        # Barra de progreso por etapas
        etapas  = ["APLICADO", "EN_ESPERA", "AVANZANDO", "CONTRATADO"]
        etapa_i = etapas.index(estado) if estado in etapas else 0
        if estado == "RECHAZADO":
            etapa_i = -1

        with st.expander(
            f"**{app['empresa']}** — {app['vacante']}  |  "
            f":{('green' if estado=='CONTRATADO' else 'red' if estado=='RECHAZADO' else 'blue')}[{estado}]  |  "
            f"{n_ents} entrevista(s)",
            expanded=False,
        ):
            # Mini progreso visual
            col_prog = st.columns(4)
            for i, etapa in enumerate(etapas):
                c = ESTADO_COLOR.get(etapa, "#94a3b8")
                activo = i <= etapa_i and estado != "RECHAZADO"
                col_prog[i].markdown(
                    f"""<div style="text-align:center;padding:6px;border-radius:8px;
                    background:{"#f0fdf4" if etapa=="CONTRATADO" and activo else c+"22" if activo else "#f1f5f9"};
                    border:2px solid {c if activo else "#e2e8f0"}">
                    <small style="font-weight:{'700' if activo else '400'};color:{c if activo else '#94a3b8'}">{etapa}</small>
                    </div>""",
                    unsafe_allow_html=True,
                )

            if estado == "RECHAZADO":
                st.error("❌ Esta aplicación fue marcada como RECHAZADA por inactividad.")

            st.markdown(f"**Modalidad:** {app['modalidad']}  |  **Origen:** {app['origen']}  |  **Fecha:** {app['fecha_aplicacion']}")
            if app.get("link"):
                st.markdown(f"🔗 [Ver oferta]({app['link']})")

            # Entrevistas de esta aplicación
            if ents:
                st.markdown("**Entrevistas registradas:**")
                for e in sorted(ents, key=lambda x: x["fecha"]):
                    tipo_icon = {"RRHH": "👥", "TECNICA": "💻", "PRUEBA_TECNICA": "📝"}.get(e["tipo"], "🗓️")
                    fecha_str = e["fecha"][:10]
                    auto_str = f" ⭐ {e['autoevaluacion']}/5" if e.get("autoevaluacion") else ""
                    grupal_str = " 👥 Grupal" if e.get("grupal") else ""
                    st.markdown(
                        f"**{tipo_icon} {e['tipo']}** — {fecha_str} — {e['modalidad']}{grupal_str}{auto_str}"
                    )    
            else:
                st.caption("Sin entrevistas aún para esta aplicación.")


# ── Bloque 3: Fallas ──────────────────────────────────────────────────────────

def _bloque_fallas(entrevistas_por_app):
    st.markdown("### ⚠️ Análisis de fallas")

    todas_ents = [e for v in entrevistas_por_app.values() for e in v]

    conteo = defaultdict(int)
    for falla_key in FALLAS_LABEL:
        conteo[falla_key] = 0  # inicializar todas en 0

    sin_fallas = 0
    for e in todas_ents:
        fallas = e.get("fallas") or []
        if not fallas:
            sin_fallas += 1
        for f in fallas:
            if f in conteo:
                conteo[f] += 1

    conteo["SIN_FALLAS"] = sin_fallas

    labels  = [FALLAS_LABEL[k] for k in conteo]
    values  = [conteo[k] for k in conteo]
    colors  = ["#22c55e" if k == "SIN_FALLAS" else "#ef4444" if v > 2 else "#f59e0b" if v > 0 else "#e2e8f0"
               for k, v in conteo.items()]

    fig = go.Figure(go.Bar(
        x=values,
        y=labels,
        orientation="h",
        marker_color=colors,
        text=values,
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Frecuencia: %{x}<extra></extra>",
    ))
    fig.update_layout(
        title="Frecuencia de fallas en entrevistas",
        xaxis_title="Cantidad de veces",
        yaxis=dict(autorange="reversed"),
        height=300,
        margin=dict(l=10, r=40, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor="#f1f5f9"),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Subfallas detalle
    subfallas_conteo = defaultdict(int)
    for e in todas_ents:
        for sf in (e.get("subfallas") or []):
            subfallas_conteo[sf] += 1

    if subfallas_conteo:
        st.markdown("**Detalle de subfallas:**")
        df_sub = pd.DataFrame(
            [(k, v) for k, v in sorted(subfallas_conteo.items(), key=lambda x: -x[1])],
            columns=["Subfalla", "Frecuencia"]
        )
        fig2 = px.treemap(
            df_sub, path=["Subfalla"], values="Frecuencia",
            color="Frecuencia",
            color_continuous_scale=["#fef3c7", "#ef4444"],
            title="Mapa de subfallas",
        )
        fig2.update_layout(
            height=250, margin=dict(l=10, r=10, t=40, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig2, use_container_width=True)


# ── Bloque 4: Reflexiones ─────────────────────────────────────────────────────

def _bloque_reflexiones(apps, entrevistas_por_app):
    st.markdown("### 💭 Mis reflexiones y aprendizajes")

    filas = []
    for app in apps:
        for e in entrevistas_por_app.get(app["id"], []):
            bien    = e.get("reflexion_bien") or ""
            mejorar = e.get("reflexion_mejorar") or ""
            if bien or mejorar:
                filas.append({
                    "fecha":    e["fecha"][:10],
                    "empresa":  app["empresa"],
                    "tipo":     e["tipo"],
                    "bien":     bien,
                    "mejorar":  mejorar,
                    "auto":     e.get("autoevaluacion") or "—",
                    "fallas":   ", ".join(e.get("fallas") or []) or "Ninguna",
                })

    if not filas:
        st.info("Aún no tienes reflexiones registradas. Completa el campo al registrar entrevistas.")
        return

    for f in sorted(filas, key=lambda x: x["fecha"], reverse=True):
        auto_val = f["auto"]
        auto_color = "#22c55e" if auto_val != "—" and int(auto_val) >= 4 else "#f59e0b" if auto_val != "—" and int(auto_val) >= 3 else "#ef4444"
        with st.container():
            st.markdown(
                f"""<div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;
                padding:16px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,.06)">
                <div style="display:flex;justify-content:space-between;margin-bottom:10px">
                    <span style="font-weight:700;color:#1e293b">{f['empresa']} — {f['tipo']}</span>
                    <span style="color:#64748b;font-size:.85rem">{f['fecha']}</span>
                </div>
                <div style="display:flex;gap:8px;margin-bottom:10px">
                    <span style="background:#fef9c3;color:#854d0e;padding:2px 8px;border-radius:99px;font-size:.75rem">
                        Fallas: {f['fallas']}
                    </span>
                    <span style="background:{auto_color}22;color:{auto_color};padding:2px 8px;border-radius:99px;font-size:.75rem;font-weight:700">
                        ⭐ Auto: {f['auto']}/5
                    </span>
                </div>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
                    <div style="background:#f0fdf4;border-radius:8px;padding:10px">
                        <p style="margin:0 0 4px;font-size:.75rem;color:#16a34a;font-weight:700">✅ Lo que hice bien</p>
                        <p style="margin:0;font-size:.85rem;color:#1e293b">{f['bien'] or '—'}</p>
                    </div>
                    <div style="background:#fff7ed;border-radius:8px;padding:10px">
                        <p style="margin:0 0 4px;font-size:.75rem;color:#ea580c;font-weight:700">📈 Por mejorar</p>
                        <p style="margin:0;font-size:.85rem;color:#1e293b">{f['mejorar'] or '—'}</p>
                    </div>
                </div>
                </div>""",
                unsafe_allow_html=True,
            )


# ── Bloque 5: Línea de tiempo ─────────────────────────────────────────────────

def _bloque_timeline(apps, entrevistas_por_app):
    st.markdown("### 📅 Línea de tiempo de actividad")

    semanas: dict = defaultdict(lambda: {"aplicaciones": 0, "entrevistas": 0})

    for app in apps:
        try:
            fecha = datetime.strptime(app["fecha_aplicacion"], "%Y-%m-%d")
            semana = fecha.strftime("%Y-W%W")
            semanas[semana]["aplicaciones"] += 1
        except Exception:
            pass

    for ents in entrevistas_por_app.values():
        for e in ents:
            try:
                fecha = datetime.fromisoformat(e["fecha"][:19])
                semana = fecha.strftime("%Y-W%W")
                semanas[semana]["entrevistas"] += 1
            except Exception:
                pass

    if not semanas:
        st.info("Sin datos de actividad aún.")
        return

    semanas_ord = sorted(semanas.keys())
    df = pd.DataFrame([
        {
            "Semana": s,
            "Aplicaciones": semanas[s]["aplicaciones"],
            "Entrevistas": semanas[s]["entrevistas"],
        }
        for s in semanas_ord
    ])

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["Semana"], y=df["Aplicaciones"],
        mode="lines+markers", name="Aplicaciones",
        line=dict(color="#3b82f6", width=2),
        marker=dict(size=7),
        fill="tozeroy", fillcolor="rgba(59,130,246,0.08)",
    ))
    fig.add_trace(go.Scatter(
        x=df["Semana"], y=df["Entrevistas"],
        mode="lines+markers", name="Entrevistas",
        line=dict(color="#8b5cf6", width=2),
        marker=dict(size=7),
        fill="tozeroy", fillcolor="rgba(139,92,246,0.08)",
    ))
    fig.update_layout(
        title="Actividad semanal",
        xaxis_title="Semana",
        yaxis_title="Cantidad",
        height=300,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor="#f1f5f9"),
        yaxis=dict(gridcolor="#f1f5f9"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)


# ── Sección perfil ────────────────────────────────────────────────────────────

def _seccion_perfil():
    st.warning("⚠️ Antes de continuar debes completar tu perfil.")
    st.subheader("📋 Completa tu perfil")

    cohortes = api.get_cohortes()
    tutores  = api.get_tutores()

    if not cohortes or not tutores:
        st.error("No hay cohortes o tutores disponibles. Contacta al coordinador.")
        return

    cohortes_activas = [c for c in cohortes if c["estado"] == "ACTIVA"]
    if not cohortes_activas:
        st.error("No hay cohortes activas. Contacta al coordinador.")
        return

    with st.form("form_perfil"):
        cohorte_map = {c["nombre"]: c["id"] for c in cohortes_activas}
        tutor_map   = {t["email"]: t["id"] for t in tutores}

        cohorte_sel = st.selectbox("Cohorte *", list(cohorte_map.keys()))
        tutor_sel   = st.selectbox("Tutor asignado *", list(tutor_map.keys()))

        col1, col2 = st.columns(2)
        with col1:
            telefono = st.text_input("Teléfono")
            ciudad   = st.text_input("Ciudad")
        with col2:
            tel_emergencia = st.text_input("Teléfono de emergencia")

        submitted = st.form_submit_button("💾 Guardar perfil", type="primary", use_container_width=True)

    if submitted:
        result = api.crear_perfil({
            "cohorte_id":          cohorte_map[cohorte_sel],
            "tutor_id":            tutor_map[tutor_sel],
            "telefono":            telefono.strip() or None,
            "telefono_emergencia": tel_emergencia.strip() or None,
            "ciudad":              ciudad.strip() or None,
        })
        if result:
            st.success("✅ Perfil completado correctamente.")
            st.rerun()


def _tab_nueva_aplicacion():
    st.subheader("➕ Registrar nueva aplicación")
    with st.form("form_nueva_app", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            empresa = st.text_input("Empresa *", placeholder="Ej: Bancolombia")
            vacante = st.text_input("Vacante / Cargo *", placeholder="Ej: Desarrollador Java Jr")
            link    = st.text_input("Link de la oferta", placeholder="https://...")
        with col2:
            modalidad = st.selectbox("Modalidad *",
                ["REMOTO","PRESENCIAL","HIBRIDO"],
                format_func=lambda x: {"REMOTO":"🌐 Remoto","PRESENCIAL":"🏢 Presencial","HIBRIDO":"🔄 Híbrido"}[x])
            origen = st.selectbox("Origen de la vacante *",
                ["PROPIA","TUTOR","EMPLEABILIDAD"],
                format_func=lambda x: {"PROPIA":"🔍 Búsqueda propia","TUTOR":"👨‍🏫 Referido por tutor","EMPLEABILIDAD":"🏫 Área de empleabilidad"}[x])
            fecha = st.date_input("Fecha de aplicación *", value=date.today())

        submitted = st.form_submit_button("📤 Registrar aplicación", type="primary", use_container_width=True)

    if submitted:
        if not empresa.strip() or not vacante.strip():
            st.error("Empresa y vacante son obligatorios.")
        else:
            result = api.crear_aplicacion({
                "empresa":          empresa.strip(),
                "vacante":          vacante.strip(),
                "modalidad":        modalidad,
                "origen":           origen,
                "fecha_aplicacion": str(fecha),
                "link":             link.strip() or None,
            })
            if result:
                st.success(f"✅ Aplicación a **{empresa}** registrada. Estado: **APLICADO**")
                st.rerun()


def _tab_perfil(perfil):
    st.subheader("👤 Mi perfil")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Ciudad:** {perfil.get('ciudad') or '—'}")
        st.markdown(f"**Teléfono:** {perfil.get('telefono') or '—'}")
    with col2:
        st.markdown(f"**Tel. emergencia:** {perfil.get('telefono_emergencia') or '—'}")

    st.divider()
    st.subheader("✏️ Actualizar datos de contacto")
    st.caption("⚠️ No puedes cambiar tu cohorte ni tu tutor asignado.")
    with st.form("form_actualizar_perfil"):
        telefono       = st.text_input("Teléfono", value=perfil.get("telefono") or "")
        tel_emergencia = st.text_input("Teléfono de emergencia", value=perfil.get("telefono_emergencia") or "")
        ciudad         = st.text_input("Ciudad", value=perfil.get("ciudad") or "")
        submitted = st.form_submit_button("💾 Guardar cambios", type="primary")

    if submitted:
        result = api.actualizar_perfil({
            "telefono":            telefono.strip() or None,
            "telefono_emergencia": tel_emergencia.strip() or None,
            "ciudad":              ciudad.strip() or None,
        })
        if result:
            st.success("✅ Perfil actualizado.")
            st.rerun()


# ── Entry point ───────────────────────────────────────────────────────────────

def show():
    st.title("📊 Mi Panel de Empleabilidad")

    perfil = api.get_mi_perfil()
    if not perfil:
        _seccion_perfil()
        return

    tab_dash, tab_vacantes, tab_fallas, tab_reflexiones, tab_timeline, \
        tab_nueva_app, tab_nueva_ent, tab_alertas, tab_perfil = st.tabs([
        "📊 Resumen",
        "📂 Mis vacantes",
        "⚠️ Fallas",
        "💭 Reflexiones",
        "📅 Actividad",
        "➕ Nueva aplicación",
        "🗓️ Nueva entrevista",
        "🔔 Alertas",
        "👤 Mi perfil",
    ])

    # Cargar datos una sola vez
    with st.spinner("Cargando datos..."):
        kpis, apps, entrevistas_por_app = _cargar_datos()

    with tab_dash:
        _bloque_semaforo(kpis, apps, entrevistas_por_app)

    with tab_vacantes:
        _bloque_vacantes(apps, entrevistas_por_app)
        st.divider()
        # Marcar contratado
        app_opts = {f"{a['empresa']} — {a['vacante']}": a["id"]
                    for a in apps if a["estado"] != "CONTRATADO"}
        if app_opts:
            st.subheader("✅ Marcar como contratado")
            seleccion = st.selectbox("Selecciona la aplicación:", list(app_opts.keys()))
            if st.button("🎉 Confirmar contratación", type="primary"):
                if api.marcar_contratado(app_opts[seleccion]):
                    st.success("¡Felicitaciones! 🎉")
                    st.rerun()

    with tab_fallas:
        fallas_show(apps, entrevistas_por_app)

    with tab_reflexiones:
        _bloque_reflexiones(apps, entrevistas_por_app)

    with tab_timeline:
        _bloque_timeline(apps, entrevistas_por_app)

    with tab_nueva_app:
        _tab_nueva_aplicacion()

    with tab_nueva_ent:
        apps_disponibles = [a for a in apps if a["estado"] != "CONTRATADO"]
        entrevista_form(apps_disponibles)

    with tab_alertas:
        alertas = api.get_alertas()
        panel_alertas(alertas)

    with tab_perfil:
        _tab_perfil(perfil)