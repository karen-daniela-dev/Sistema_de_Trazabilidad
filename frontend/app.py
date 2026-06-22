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
    .stApp { background: #f8fafc !important; }
    .stApp * { color: #1e293b !important; }
    .block-container { padding-top: 1.5rem; }
    
    /* Inputs */
    .stTextInput > div > div > input {
        border-radius: 8px;
        color: #1e293b !important;
        background: #ffffff !important;
    }
    
    /* Botón primario */
    .stButton > button {
        background: #1a56db !important;
        color: #ffffff !important;
        border: none;
        border-radius: 8px;
        font-weight: 600;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab"] {
        font-weight: 500;
        color: #1e293b !important;
    }

 /* Sidebar */
    [data-testid="stSidebar"] {
        background: #1e293b !important;
    }
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] button {
        color: #e2e8f0 !important;
    }
    /* Botón sidebar (cerrar sesión) */
    [data-testid="stSidebar"] button {
        color: #e2e8f0 !important;
        border-color: #e2e8f0 !important;
    }
    [data-testid="stSidebar"] button:hover {
        background: #334155 !important;
        color: #ffffff !important;
    }
    
    /* Botón header (hamburguesa) */
    button[data-testid="baseButton-header"] {
        color: #1e293b !important;
    }
    button[data-testid="baseButton-header"] svg {
        fill: #1e293b !important;
        stroke: #1e293b !important;
    }

    /* Ocultar menú */
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
