"""
Página de login y registro de aprendiz.
"""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from frontend import api_client as api


def show():
    st.markdown("""
    <div style="text-align:center;padding:40px 0 20px">
        <h1 style="color:#1a56db;font-size:2rem;font-weight:800">
            🎓 Sistema de Empleabilidad
        </h1>
        <p style="color:#64748b">Full Stack Java Bootcamp</p>
    </div>
    """, unsafe_allow_html=True)

    tab_login, tab_registro = st.tabs(["Iniciar sesión", "Registrarse (Aprendiz)"])

    with tab_login:
        with st.form("form_login"):
            email = st.text_input("Email", placeholder="tu@email.com")
            password = st.text_input("Contraseña", type="password")
            submitted = st.form_submit_button("Entrar", use_container_width=True, type="primary")

        if submitted:
            if not email or not password:
                st.error("Completa todos los campos.")
            else:
                with st.spinner("Verificando..."):
                    result = api.login(email, password)
                if result:
                    st.session_state["token"] = result["access_token"]
                    st.session_state["rol"] = result["rol"]
                    st.session_state["user_id"] = result["user_id"]
                    st.success("✅ Sesión iniciada")
                    st.rerun()

    with tab_registro:
        st.info("Solo para aprendices. Los tutores reciben activación por email.")
        with st.form("form_registro"):
            email_r = st.text_input("Email", key="reg_email")
            pwd_r = st.text_input("Contraseña", type="password", key="reg_pwd")
            pwd_c = st.text_input("Confirmar contraseña", type="password", key="reg_pwd2")
            st.caption("Mínimo 8 caracteres, una mayúscula, una minúscula, un número y un carácter especial.")
            sub_r = st.form_submit_button("Registrarme", use_container_width=True)

        if sub_r:
            if not email_r or not pwd_r:
                st.error("Completa todos los campos.")
            elif pwd_r != pwd_c:
                st.error("Las contraseñas no coinciden.")
            else:
                with st.spinner("Creando cuenta..."):
                    result = api.register_aprendiz(email_r, pwd_r)
                if result:
                    st.success("✅ Cuenta creada. Ahora inicia sesión.")
