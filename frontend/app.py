"""
Punto de entrada Streamlit.
Enruta a la página correcta según el rol del usuario autenticado.
"""
import streamlit as st
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from frontend.pages import login
from frontend.pages.aprendiz import dashboard as aprendiz_dashboard
from frontend.pages.tutor import dashboard as tutor_dashboard
from frontend.pages.coordinador import dashboard as coordinador_dashboard

st.set_page_config(
    page_title="Sistema de Empleabilidad",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS Global ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Fuente y fondo */
    .stApp { background: #f8fafc; }
    .block-container { padding-top: 1.5rem; }

    /* Botón primario */
    .stButton > button[data-testid="baseButton-primary"] {
        background: #1a56db;
        border: none;
        border-radius: 8px;
        font-weight: 600;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab"] {
        font-weight: 500;
    }

    /* Inputs */
    .stTextInput > div > div > input {
        border-radius: 8px;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #1e293b;
    }
    [data-testid="stSidebar"] * {
        color: #e2e8f0 !important;
    }

    /* Ocultar el menú de Streamlit en producción */
    #MainMenu { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ── Enrutador principal ───────────────────────────────────────────────────────

def main():
    token = st.session_state.get("token")
    rol = st.session_state.get("rol")

    if not token:
        login.show()
        return

    # Sidebar con info de sesión
    with st.sidebar:
        st.markdown("### 🎓 Empleabilidad")
        st.markdown(f"**Rol:** {rol}")
        st.markdown(f"**ID:** `{str(st.session_state.get('user_id', ''))[:8]}...`")
        st.divider()
        if st.button("🚪 Cerrar sesión", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    # Enrutar por rol
    if rol == "COORDINADOR":
        coordinador_dashboard.show()
    elif rol == "TUTOR":
        tutor_dashboard.show()
    elif rol == "APRENDIZ":
        aprendiz_dashboard.show()
    else:
        st.error("Rol no reconocido. Cierra sesión e intenta de nuevo.")


if __name__ == "__main__":
    main()
