import streamlit as st
import pandas as pd

from frontend import api_client as api
#pages/coordinador/cohorte_detail

SEMAFORO_EMOJI = {
    "GREEN": "🟢",
    "YELLOW": "🟡",
    "RED": "🔴",
}


def show(cohorte_id: str):
    with st.spinner("Cargando detalle de cohorte..."):
        data = api.get_kpis_detalle_cohorte(cohorte_id)

    if not data:
        st.error("No se pudo cargar la cohorte.")
        return

    cohorte = data["cohorte"]
    stats = data["stats"]
    aprendices = data["aprendices"]

    # ── Header ─────────────────────────────────────────────
    st.title(f"📘 Cohorte: {cohorte['nombre']}")

    col1, col2 = st.columns(2)
    col1.info(f"Estado: {cohorte['estado']}")
    col2.info(f"Meta contratación: {cohorte['meta']}")

    st.divider()

    # ── KPIs ───────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Aprendices", stats["total_aprendices"])
    c2.metric("Aplicaciones", stats["total_aplicaciones"])
    c3.metric("Contratados", stats["contratados"])
    c4.metric("Tasa contratación", f"{stats['tasa_contratacion']:.0%}")

    st.divider()

    # ── Semáforos Globales ─────────────────────────────────
    c1, c2 = st.columns(2)

    c1.metric("Actividad Verde", stats["actividad_green"])
    c2.metric("Progreso Verde", stats["progreso_green"])

    st.divider()

    # ── Tabla Analytics ────────────────────────────────────
    st.subheader("📊 Deep Analytics")

    filas = []
    for a in aprendices:
        filas.append({
            "Aprendiz": a["email"],
            "Tutor": a["tutor_email"],
            "Apps": a["total_aplicaciones"],
            "Entrevistas": a["total_entrevistas"],
            "Contratado": "✅" if a["contratado"] else "—",
            "Actividad": SEMAFORO_EMOJI.get(a["semaforo_actividad"], "⚪"),
            "Progreso": SEMAFORO_EMOJI.get(a["semaforo_progreso"], "⚪"),
        })

    df = pd.DataFrame(filas)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )