"""
Tests de seguridad — RBAC, JWT, inyección, acceso cruzado.
"""
import pytest
from backend.tests.conftest import auth_headers, make_usuario
from backend.models.enums import RolEnum


class TestRBAC:
    """Verifica que los roles no puedan acceder a recursos de otros roles."""

    def test_aprendiz_no_accede_a_kpis_globales(self, client, aprendiz):
        r = client.get("/kpis/global", headers=auth_headers(aprendiz))
        assert r.status_code == 403

    def test_tutor_no_accede_a_kpis_globales(self, client, tutor):
        r = client.get("/kpis/global", headers=auth_headers(tutor))
        assert r.status_code == 403

    def test_aprendiz_no_crea_cohortes(self, client, aprendiz):
        r = client.post("/cohortes/", json={
            "nombre": "Hack cohorte",
            "fecha_inicio": "2024-01-01",
            "meta_contratacion": 10,
        }, headers=auth_headers(aprendiz))
        assert r.status_code == 403

    def test_tutor_no_crea_cohortes(self, client, tutor):
        r = client.post("/cohortes/", json={
            "nombre": "Hack cohorte",
            "fecha_inicio": "2024-01-01",
            "meta_contratacion": 10,
        }, headers=auth_headers(tutor))
        assert r.status_code == 403

    def test_aprendiz_no_crea_tutores(self, client, aprendiz):
        r = client.post("/usuarios/tutor", json={"email": "hack@tutor.com"},
                        headers=auth_headers(aprendiz))
        assert r.status_code == 403

    def test_tutor_no_crea_tutores(self, client, tutor):
        r = client.post("/usuarios/tutor", json={"email": "hack@tutor.com"},
                        headers=auth_headers(tutor))
        assert r.status_code == 403

    def test_sin_token_todo_protegido(self, client):
        endpoints = [
            ("GET", "/auth/me"),
            ("GET", "/aplicaciones/"),
            ("GET", "/kpis/global"),
            ("GET", "/cohortes/"),
        ]
        for method, url in endpoints:
            r = client.request(method, url)
            assert r.status_code == 401, f"{method} {url} debería retornar 401"

    def test_token_expirado_rechazado(self, client):
        from datetime import timedelta
        from backend.utils.security import create_access_token
        from backend.models.enums import RolEnum
        token = create_access_token(
            {"sub": "fake-id", "rol": RolEnum.COORDINADOR.value},
            expires_delta=timedelta(seconds=-1),
        )
        r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 401


class TestJWTSecurity:
    def test_token_manipulado_rechazado(self, client, aprendiz):
        token = auth_headers(aprendiz)["Authorization"].replace("Bearer ", "")
        partes = token.split(".")
        # Modificar el payload para intentar escalar privilegios
        import base64, json
        payload = json.loads(base64.urlsafe_b64decode(partes[1] + "=="))
        payload["rol"] = "COORDINADOR"
        payload_mod = base64.urlsafe_b64encode(
            json.dumps(payload).encode()
        ).decode().rstrip("=")
        token_mod = f"{partes[0]}.{payload_mod}.{partes[2]}"
        r = client.get("/kpis/global", headers={"Authorization": f"Bearer {token_mod}"})
        assert r.status_code == 401

    def test_token_sin_sub_rechazado(self, client):
        from backend.utils.security import create_access_token
        token = create_access_token({"rol": "COORDINADOR"})  # sin sub
        r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 401

    def test_token_algoritmo_none_rechazado(self, client):
        """Previene el ataque clásico 'alg: none'."""
        import base64, json
        header = base64.urlsafe_b64encode(json.dumps({"alg": "none", "typ": "JWT"}).encode()).decode().rstrip("=")
        payload = base64.urlsafe_b64encode(json.dumps({"sub": "hacker", "rol": "COORDINADOR"}).encode()).decode().rstrip("=")
        token = f"{header}.{payload}."
        r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 401


class TestInjectionPrevention:
    """Verifica que inputs maliciosos son rechazados o saneados."""

    def test_sql_injection_en_login(self, client):
        r = client.post("/auth/login", data={
            "username": "admin'--",
            "password": "anything",
        })
        # Debe fallar por credenciales, no revelar error SQL
        assert r.status_code == 401
        assert "sql" not in r.text.lower()

    def test_xss_en_empresa(self, client, setup_aprendiz_completo):
        aprendiz, *_ = setup_aprendiz_completo
        r = client.post("/aplicaciones/", json={
            "empresa": "<script>alert('xss')</script>",
            "vacante": "Dev",
            "modalidad": "REMOTO",
            "origen": "PROPIA",
        }, headers=auth_headers(aprendiz))
        # Se almacena como texto (no ejecutable) — la API JSON no renderiza HTML
        # Lo importante: no falla con 500 y el contenido se trata como string
        assert r.status_code in (201, 422)

    def test_payload_gigante_rechazado(self, client):
        r = client.post("/auth/login", data={
            "username": "a" * 10_000 + "@test.com",
            "password": "Test@1234",
        })
        assert r.status_code in (401, 422, 413)

    def test_campo_estado_no_aceptado_en_aplicacion(self, client, setup_aprendiz_completo):
        """El cliente NO puede definir el estado de una aplicación."""
        aprendiz, *_ = setup_aprendiz_completo
        r = client.post("/aplicaciones/", json={
            "empresa": "Corp",
            "vacante": "Dev",
            "modalidad": "REMOTO",
            "origen": "PROPIA",
            "estado": "CONTRATADO",  # intento de bypass
        }, headers=auth_headers(aprendiz))
        if r.status_code == 201:
            # Si se creó, el estado debe ser APLICADO (ignoró el campo)
            assert r.json()["estado"] == "APLICADO"


class TestAccessControl:
    def test_aprendiz_no_edita_cohorte_ni_tutor_en_perfil(self, client, setup_aprendiz_completo, db):
        aprendiz, _, cohorte, _ = setup_aprendiz_completo
        # Crear otra cohorte para intentar cambiarse
        otra = make_usuario(db, rol=RolEnum.COORDINADOR)
        r = client.patch("/usuarios/perfil/me", json={
            "ciudad": "Medellín",
            "cohorte_id": "00000000-0000-0000-0000-000000000000",  # intento
            "tutor_id": "00000000-0000-0000-0000-000000000001",
        }, headers=auth_headers(aprendiz))
        if r.status_code == 200:
            # Si aceptó, cohorte y tutor deben ser los originales
            perfil = client.get("/usuarios/perfil/me", headers=auth_headers(aprendiz)).json()
            assert str(perfil["cohorte_id"]) == str(cohorte.id)

    def test_headers_seguridad_presentes(self, client):
        r = client.get("/")
        assert r.headers.get("x-content-type-options") == "nosniff"
        assert r.headers.get("x-frame-options") == "DENY"
