"""
Componentes UI reutilizables — usados en todas las páginas.
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# ── Paleta del sistema ────────────────────────────────────────────────────────
COLORES = {
    "GREEN": "#16a34a",
    "YELLOW": "#ca8a04",
    "RED": "#dc2626",
    "primary": "#1a56db",
    "bg": "#f8fafc",
}

ESTADO_LABELS = {
    "APLICADO": ("📋", "#64748b"),
    "EN_ESPERA": ("⏳", "#2563eb"),
    "AVANZANDO": ("🚀", "#7c3aed"),
    "RECHAZADO": ("❌", "#dc2626"),
    "CONTRATADO": ("🎉", "#16a34a"),
}


# ── Semáforo visual ───────────────────────────────────────────────────────────

def semaforo_badge(valor: str, texto: str = "") -> str:
    """Retorna HTML de badge coloreado."""
    color = COLORES.get(valor, "#94a3b8")
    emoji = {"GREEN": "🟢", "YELLOW": "🟡", "RED": "🔴"}.get(valor, "⚪")
    label = {"GREEN": "Al día", "YELLOW": "Atención", "RED": "Crítico"}.get(valor, valor)
    return f"{emoji} **{label}**" + (f" — {texto}" if texto else "")


def mostrar_semaforo(valor: str, titulo: str = "Estado"):
    color = COLORES.get(valor, "#94a3b8")
    emoji = {"GREEN": "🟢", "YELLOW": "🟡", "RED": "🔴"}.get(valor, "⚪")
    label = {"GREEN": "Al día", "YELLOW": "Requiere atención", "RED": "Crítico"}.get(valor, valor)
    st.markdown(
        f"""<div style="background:{color}22;border-left:4px solid {color};
        padding:12px 16px;border-radius:6px;margin:8px 0">
        <span style="font-size:1.2em">{emoji}</span>
        <strong style="color:{color};margin-left:8px">{titulo}: {label}</strong>
        </div>""",
        unsafe_allow_html=True,
    )


# ── KPI Cards ─────────────────────────────────────────────────────────────────

def kpi_card(col, titulo: str, valor, subtitulo: str = "", color: str = "#1a56db"):
    col.markdown(
        f"""<div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;
        padding:20px;text-align:center;box-shadow:0 1px 3px rgba(0,0,0,.08)">
        <p style="color:#64748b;font-size:.8rem;margin:0;text-transform:uppercase;
        letter-spacing:.05em">{titulo}</p>
        <p style="color:{color};font-size:2rem;font-weight:700;margin:4px 0">{valor}</p>
        <p style="color:#94a3b8;font-size:.75rem;margin:0">{subtitulo}</p>
        </div>""",
        unsafe_allow_html=True,
    )


# ── Estado de aplicación ──────────────────────────────────────────────────────

def estado_badge(estado: str) -> str:
    emoji, color = ESTADO_LABELS.get(estado, ("❓", "#64748b"))
    return f"{emoji} {estado}"


# ── Tabla paginada ────────────────────────────────────────────────────────────

def tabla_aplicaciones(items: list[dict], mostrar_usuario: bool = False):
    if not items:
        st.info("No hay aplicaciones registradas aún.")
        return

    columnas = {
        "empresa": "Empresa",
        "vacante": "Vacante",
        "modalidad": "Modalidad",
        "fecha_aplicacion": "Fecha",
        "origen": "Origen",
        "estado": "Estado",
    }
    if mostrar_usuario:
        columnas["usuario_id"] = "Aprendiz"

    df = pd.DataFrame(items)[list(columnas.keys())]
    df.columns = list(columnas.values())
    df["Estado"] = df["Estado"].apply(estado_badge)
    st.dataframe(df, use_container_width=True, hide_index=True)


# ── Gráficos ──────────────────────────────────────────────────────────────────

def chart_estados_pie(por_estado: dict):
    labels = list(por_estado.keys())
    values = list(por_estado.values())
    colores_pie = {
        "APLICADO": "#94a3b8", "EN_ESPERA": "#2563eb",
        "AVANZANDO": "#7c3aed", "RECHAZADO": "#dc2626", "CONTRATADO": "#16a34a",
    }
    fig = go.Figure(go.Pie(
        labels=labels, values=values,
        marker_colors=[colores_pie.get(l, "#ccc") for l in labels],
        hole=0.45, textinfo="label+percent",
    ))
    fig.update_layout(
        title="Distribución por estado", showlegend=False,
        margin=dict(t=40, b=10, l=10, r=10), height=300,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)


def chart_fallas_bar(fallas: list[tuple]):
    if not fallas:
        st.info("Sin datos de fallas aún.")
        return
    df = pd.DataFrame(fallas, columns=["Falla", "Frecuencia"])
    fig = px.bar(df, x="Falla", y="Frecuencia", color="Frecuencia",
                 color_continuous_scale=["#bfdbfe", "#1d4ed8"],
                 title="Fallas más frecuentes")
    fig.update_layout(
        showlegend=False, coloraxis_showscale=False,
        margin=dict(t=40, b=10, l=10, r=10), height=300,
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)


def chart_semaforos_grupo(resumen: dict):
    categorias = ["🟢 Al día", "🟡 Atención", "🔴 Crítico"]
    valores = [resumen.get("GREEN", 0), resumen.get("YELLOW", 0), resumen.get("RED", 0)]
    colores = [COLORES["GREEN"], COLORES["YELLOW"], COLORES["RED"]]
    fig = go.Figure(go.Bar(
        x=categorias, y=valores,
        marker_color=colores,
        text=valores, textposition="outside",
    ))
    fig.update_layout(
        title="Estado del grupo", yaxis_title="Aprendices",
        margin=dict(t=40, b=10, l=10, r=10), height=300,
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)


def chart_cohortes_barras(cohortes: list[dict]):
    if not cohortes:
        return
    df = pd.DataFrame(cohortes)
    fig = go.Figure()
    fig.add_bar(name="Contratados", x=df["nombre"], y=df["contratados"],
                marker_color=COLORES["GREEN"])
    fig.add_bar(name="Meta", x=df["nombre"], y=df["meta"],
                marker_color="#cbd5e1")
    fig.update_layout(
        barmode="overlay", title="Contratados vs Meta por cohorte",
        margin=dict(t=40, b=10, l=10, r=10), height=320,
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)


# ── Alertas panel ─────────────────────────────────────────────────────────────

def panel_alertas(alertas: list[dict]):
    tipos_iconos = {
        "INACTIVIDAD": "😴",
        "BAJA_CONVERSION": "📉",
        "MULTIPLES_RECHAZOS": "⚠️",
        "COHORTE_RED": "🚨",
        "COHORTE_YELLOW": "⚠️",
    }
    if not alertas:
        st.success("✅ Sin alertas pendientes.")
        return
    st.markdown(f"**{len(alertas)} alerta(s) activa(s)**")
    for a in alertas[:10]:
        icono = tipos_iconos.get(a.get("tipo", ""), "🔔")
        with st.container():
            st.markdown(
                f"""<div style="background:#fff7ed;border-left:3px solid #f97316;
                padding:10px 14px;border-radius:6px;margin:4px 0">
                {icono} {a.get('mensaje', '')}
                </div>""",
                unsafe_allow_html=True,
            )


def chart_funnel_global(kpis: dict):
    labels = ["Aprendices", "Aplicaciones", "Entrevistas", "Contratados"]
    values = [
        kpis.get("total_aprendices", 0),
        kpis.get("total_aplicaciones", 0),
        kpis.get("total_entrevistas", 0),
        kpis.get("contratados_total", 0),
    ]

    fig = go.Figure(go.Funnel(
        y=labels,
        x=values,
        textinfo="value+percent initial"
    ))

    fig.update_layout(
        title="Embudo Global",
        height=420
    )

    st.plotly_chart(fig, use_container_width=True)
    
def chart_cohortes_comparativo(cohortes):
    if not cohortes:
        st.info("Sin cohortes.")
        return

    df = pd.DataFrame(cohortes)

    fig = go.Figure()
    fig.add_bar(name="Contratados", x=df["nombre"], y=df["contratados"])
    fig.add_bar(name="Meta", x=df["nombre"], y=df["meta"])

    fig.update_layout(
        title="Cohortes: Contratados vs Meta",
        barmode="group",
        height=420
    )
    st.plotly_chart(fig, use_container_width=True)

def chart_ranking_tutores(ranking):
    if not ranking:
        st.info("Sin tutores.")
        return

    df = pd.DataFrame(ranking[:10])

    fig = px.bar(
        df,
        x="email",
        y="score",
        title="Top Tutores",
        text="score"
    )

    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)



    
def chart_estado_apps(kpis):
    labels = ["Aplicaciones", "Entrevistas", "Contratados"]
    values = [
        kpis.get("total_aplicaciones", 0),
        kpis.get("total_entrevistas", 0),
        kpis.get("contratados_total", 0),
    ]

    fig = px.pie(
        names=labels,
        values=values,
        title="Distribución Global"
    )

    fig.update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True)
    
def chart_top_fallas(fallas):
    if not fallas:
        st.info("Sin datos.")
        return

    df = pd.DataFrame(fallas, columns=["Falla", "Cantidad"])

    fig = px.bar(
        df,
        x="Falla",
        y="Cantidad",
        title="Top Fallas"
    )

    fig.update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True)

