"""
Tab de fallas — 4 tortas + selectbox para drill-down confiable.
"""
from collections import defaultdict

import streamlit as st
import plotly.graph_objects as go

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
    datos = {k: [] for k in FALLAS_CONFIG}
    subfallas_por_falla = {k: defaultdict(int) for k in FALLAS_CONFIG}

    for app in apps:
        for entrevista in entrevistas_por_app.get(app["id"], []):
            fallas = entrevista.get("fallas") or []
            fecha_raw = entrevista.get("fecha") or ""
            subfallas = entrevista.get("subfallas") or []
            for falla in fallas:
                if falla not in datos:
                    continue

                datos[falla].append({
                    "empresa": app["empresa"],
                    "vacante": app["vacante"],
                    "fecha": fecha_raw[:10],
                    "fecha_sort": fecha_raw,
                    "tipo": entrevista.get("tipo"),
                    "mejorar": entrevista.get("reflexion_mejorar") or "—",
                    "auto": entrevista.get("autoevaluacion") or "—",
                })

                if subfallas:
                    for subfalla in subfallas:
                        subfallas_por_falla[falla][subfalla] += 1
                else:
                    subfallas_por_falla[falla]["Sin subfalla especificada"] += 1

    for falla_key in datos:
        datos[falla_key].sort(key=lambda item: item["fecha_sort"], reverse=True)

    return datos, subfallas_por_falla


def _make_pie(cfg, subfallas):
    if not subfallas:
        fig = go.Figure(go.Pie(
            labels=["Sin subfallas"], values=[1],
            marker_colors=["#e2e8f0"], hole=0.5,
            textinfo="label", hoverinfo="skip",
        ))
    else:
        labels = list(subfallas.keys())
        values = list(subfallas.values())
        fig = go.Figure(go.Pie(
            labels=labels, values=values,
            marker_colors=COLORES_PIE[:len(labels)], hole=0.45,
            textinfo="label+percent",
            hovertemplate="<b>%{label}</b><br>Ocurrencias: %{value}<extra></extra>",
        ))
    fig.update_layout(
        title=dict(text=cfg["label"], font=dict(size=14)),
        height=260, margin=dict(l=10, r=10, t=50, b=10),
        paper_bgcolor="rgba(0,0,0,0)", showlegend=False,
    )
    return fig


@st.fragment
def _render_detalle_falla(cfg, registros):
    if "falla_detail_page" not in st.session_state:
        st.session_state.falla_detail_page = 1
    if "falla_detail_sel" not in st.session_state:
        st.session_state.falla_detail_sel = ""

    page = st.session_state.falla_detail_page
    page_size = 5
    total_pages = max(1, (len(registros) + page_size - 1) // page_size)
    inicio = (page - 1) * page_size
    fin = inicio + page_size
    pagina = registros[inicio:fin]

    st.markdown(
        f"""<div style="background:{cfg['color']}15;border-left:4px solid {cfg['color']};
        padding:10px 16px;border-radius:8px;margin:12px 0">
        <strong style="color:{cfg['color']}">{cfg['label']}</strong>
        &nbsp;·&nbsp; {len(registros)} ocurrencia(s)
        </div>""",
        unsafe_allow_html=True,
    )

    for r in pagina:
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

    if total_pages > 1:
        st.markdown("""<div style='margin-top:18px;padding-top:12px;border-top:1px solid #e2e8f0;'></div>""", unsafe_allow_html=True)
        col_prev, col_center, col_next = st.columns([1, 2, 1])
        with col_prev:
            if st.button("← Anterior", key="falla_detail_prev", disabled=page <= 1, use_container_width=True):
                st.session_state.falla_detail_page = max(1, page - 1)
        with col_center:
            st.markdown(
                f"<div style='text-align:center;color:#475569;font-size:0.92rem;font-weight:600'>Página {page} de {total_pages}</div>",
                unsafe_allow_html=True,
            )
        with col_next:
            if st.button("Siguiente →", key="falla_detail_next", disabled=page >= total_pages, use_container_width=True):
                st.session_state.falla_detail_page = min(total_pages, page + 1)


def show(apps, entrevistas_por_app):
    st.markdown("### ⚠️ Análisis de fallas")

    datos, subfallas_por_falla = _construir_datos(apps, entrevistas_por_app)
    fallas_list = list(FALLAS_CONFIG.keys())

    # ── 4 tortas en grid 2x2 ─────────────────────────────────────────────────
    col1, col2 = st.columns(2)
    columnas   = [col1, col2, col1, col2]

    for i, falla_key in enumerate(fallas_list):
        cfg = FALLAS_CONFIG[falla_key]
        with columnas[i]:
            st.plotly_chart(
                _make_pie(cfg, subfallas_por_falla[falla_key]),
                use_container_width=True,
                key=f"pie_{falla_key}",
            )

    # ── Selector de drill-down ────────────────────────────────────────────────
    st.divider()
    st.markdown("### 🔍 Ver detalle por falla")

    fallas_con_datos = [k for k in fallas_list if datos[k]]

    if not fallas_con_datos:
        st.info("Aún no tienes fallas registradas en tus entrevistas.")
        return

    falla_sel = st.selectbox(
        "Selecciona la falla:",
        [""] + fallas_con_datos,
        format_func=lambda x: "— Elige una falla —" if not x else FALLAS_CONFIG[x]["label"],
        key="drill_falla",
    )

    if falla_sel:
        cfg = FALLAS_CONFIG[falla_sel]
        registros = datos[falla_sel]

        if st.session_state.get("falla_detail_sel") != falla_sel:
            st.session_state.falla_detail_sel = falla_sel
            st.session_state.falla_detail_page = 1

        _render_detalle_falla(cfg, registros)