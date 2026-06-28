"""
Resumen superior del Dashboard Tutor.
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

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Meta",
        f'{goal["porcentaje_meta"]:.0f}%',
    )

    c2.metric(
        "Actual",
        f'{goal["porcentaje_actual"]:.1f}%',
    )

    c3.metric(
        "Cumplimiento",
        f'{goal["porcentaje_cumplimiento"]:.1f}%',
    )

    st.caption(

        f'{goal["contratados"]} contratados de '

        f'{goal["meta_contratados"]} esperados.'
    )

    st.divider()

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Aprendices",
        cards["total_aprendices"],
    )

    c2.metric(
        "Contratados",
        cards["contratados"],
    )

    c3.metric(
        "Tasa",
        f'{cards["tasa_contratacion"]:.1f}%',
    )

    c4.metric(
        "Meta restante",
        goal["faltantes"],
    )