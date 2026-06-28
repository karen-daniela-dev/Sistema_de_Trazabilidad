"""
Resumen superior del Dashboard Tutor.
Tarjetas visuales usando st.container(border=True) nativo de Streamlit.
"""

import streamlit as st


def show(summary: dict):

    goal = summary["goal"]
    cards = summary["cards"]

    st.subheader("🎯 Cumplimiento de meta")

    st.progress(
        min(
            goal["porcentaje_cumplimiento"],
            100,
        ) / 100,
    )

    # Tarjeta de progreso con border nativo
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        
        with c1:
            st.metric(
                "📊 Meta",
                f'{goal["porcentaje_meta"]:.0f}%',
            )

        with c2:
            st.metric(
                "📈 Actual",
                f'{goal["porcentaje_actual"]:.1f}%',
            )

        with c3:
            st.metric(
                "✅ Cumplimiento",
                f'{goal["porcentaje_cumplimiento"]:.1f}%',
            )

    st.caption(
        f'{goal["contratados"]} contratados de '
        f'{goal["meta_contratados"]} esperados.'
    )

    st.divider()

    # Tarjeta de KPIs con border nativo
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.metric(
                "👥 Aprendices",
                cards["total_aprendices"],
            )

        with c2:
            st.metric(
                "🎯 Contratados",
                cards["contratados"],
            )

        with c3:
            st.metric(
                "📊 Tasa",
                f'{cards["tasa_contratacion"]:.1f}%',
            )

        with c4:
            st.metric(
                "🎯 Faltantes",
                goal["faltantes"],
            )