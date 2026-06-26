"""
Tab de fallas — 4 tortas + selectbox para drill-down confiable.
"""
import streamlit as st
import plotly.graph_objects as go
from collections import defaultdict

FALLAS_CONFIG = {
    "TECNICA":              {"label": "💻 Técnica",              "color": "#3b82f6"},
    "COMUNICACION":         {"label": "🗣️ Comunicación",         "color": "#8b5cf6"},
    "BLANDAS":              {"label": "🤝 Habilidades blandas",  "color": "#f59e0b"},
    "REGULACION_EMOCIONAL": {"label": "🧘 Regulación emocional", "color": "#ef4444"},
}

COLORES_PIE = [
    "#3b82f6","#8b5cf6","#f59e0b","#ef4444","#22c55e",
    "#06b6d4","#f97316","#a855f7","#84cc16","#ec4899",
]


def _construir_datos(apps, entrevistas_por_app):
    datos = {k: defaultdict(list) for k in FALLAS_CONFIG}
    for app in apps:
        for e in entrevistas_por_app.get(app["id"], []):
            fallas    = e.get("fallas") or []
            subfallas = e.get("subfallas") or []
            for falla in fallas:
                if falla not in datos:
                    continue
                subs = subfallas if subfallas else ["Sin subfalla especificada"]
                for sub in subs:
                    datos[falla][sub].append({
                        "empresa": app["empresa"],
                        "vacante": app["vacante"],
                        "fecha":   e["fecha"][:10],
                        "tipo":    e["tipo"],
                        "mejorar": e.get("reflexion_mejorar") or "—",
                        "auto":    e.get("autoevaluacion") or "—",
                    })
    return datos


def _make_pie(cfg, subfallas):
    if not subfallas:
        fig = go.Figure(go.Pie(
            labels=["Sin registros"], values=[1],
            marker_colors=["#e2e8f0"], hole=0.5,
            textinfo="label", hoverinfo="skip",
        ))
    else:
        labels = list(subfallas.keys())
        values = [len(v) for v in subfallas.values()]
        fig = go.Figure(go.Pie(
            labels=labels, values=values,
            marker_colors=COLORES_PIE[:len(labels)],
            hole=0.45, textinfo="label+percent",
            hovertemplate="<b>%{label}</b><br>Ocurrencias: %{value}<extra></extra>",
        ))
    fig.update_layout(
        title=dict(text=cfg["label"], font=dict(size=14)),
        height=260, margin=dict(l=10, r=10, t=50, b=10),
        paper_bgcolor="rgba(0,0,0,0)", showlegend=False,
    )
    return fig


def show(apps, entrevistas_por_app):
    st.markdown("### ⚠️ Análisis de fallas")

    datos       = _construir_datos(apps, entrevistas_por_app)
    fallas_list = list(FALLAS_CONFIG.keys())

    # ── 4 tortas en grid 2x2 ─────────────────────────────────────────────────
    col1, col2 = st.columns(2)
    columnas   = [col1, col2, col1, col2]

    for i, falla_key in enumerate(fallas_list):
        cfg = FALLAS_CONFIG[falla_key]
        with columnas[i]:
            st.plotly_chart(
                _make_pie(cfg, datos[falla_key]),
                use_container_width=True,
                key=f"pie_{falla_key}",
            )

    # ── Selector de drill-down ────────────────────────────────────────────────
    st.divider()
    st.markdown("### 🔍 Ver detalle por falla y subfalla")

    # Fallas que tienen datos
    fallas_con_datos = [k for k in fallas_list if datos[k]]

    if not fallas_con_datos:
        st.info("Aún no tienes fallas registradas en tus entrevistas.")
        return

    col_f, col_s = st.columns(2)

    with col_f:
        falla_sel = st.selectbox(
            "Selecciona la falla:",
            [""] + fallas_con_datos,
            format_func=lambda x: "— Elige una falla —" if not x else FALLAS_CONFIG[x]["label"],
            key="drill_falla",
        )

    subfallas_disponibles = list(datos[falla_sel].keys()) if falla_sel else []

    with col_s:
        subfalla_sel = st.selectbox(
            "Selecciona la subfalla:",
            [""] + subfallas_disponibles,
            format_func=lambda x: "— Elige una subfalla —" if not x else x,
            key="drill_subfalla",
        ) if subfallas_disponibles else None

    # ── Resultados ────────────────────────────────────────────────────────────
    if falla_sel and subfalla_sel:
        cfg       = FALLAS_CONFIG[falla_sel]
        registros = datos[falla_sel].get(subfalla_sel, [])

        st.markdown(
            f"""<div style="background:{cfg['color']}15;border-left:4px solid {cfg['color']};
            padding:10px 16px;border-radius:8px;margin:12px 0">
            <strong style="color:{cfg['color']}">{cfg['label']}</strong>
            → <strong>{subfalla_sel}</strong>
            &nbsp;·&nbsp; {len(registros)} ocurrencia(s)
            </div>""",
            unsafe_allow_html=True,
        )

        for r in registros:
            auto_str = f"⭐ {r['auto']}/5" if r['auto'] != "—" else ""
            st.markdown(
                f"""<div style="background:#fff;border:1px solid #e2e8f0;
                border-radius:10px;padding:14px;margin-bottom:8px;
                box-shadow:0 1px 3px rgba(0,0,0,.06)">
                <div style="display:flex;justify-content:space-between;margin-bottom:8px">
                    <span style="font-weight:700;color:#1e293b">{r['empresa']} — {r['vacante']}</span>
                    <span style="color:#64748b;font-size:.82rem">{r['fecha']} · {r['tipo']} {auto_str}</span>
                </div>
                <div style="background:#fff7ed;border-radius:6px;padding:8px 12px">
                    <span style="font-size:.75rem;color:#ea580c;font-weight:700">📈 Por mejorar:</span>
                    <span style="font-size:.85rem;color:#1e293b;margin-left:6px">{r['mejorar']}</span>
                </div>
                </div>""",
                unsafe_allow_html=True,
            )