"""
Tests de integración — Endpoints de autenticación.
"""
from backend.tests.conftest import make_usuario, auth_headers
from backend.models.enums import RolEnum, EstadoUsuario


class TestRegisterAprendiz:
    def test_registro_exitoso(self, client):
        r = client.post("/auth/register", json={
            "email": "nuevo@test.com",
            "password": "Test@1234",
        })
        assert r.status_code == 201
        data = r.json()
        assert data["email"] == "nuevo@test.com"
        assert data["rol"] == "APRENDIZ"
        assert data["estado"] == "ACTIVO"

    def test_email_duplicado_falla(self, client, aprendiz):
        r = client.post("/auth/register", json={
            "email": aprendiz.email,
            "password": "Test@1234",
        })
        assert r.status_code == 400
        assert "registrado" in r.json()["detail"].lower()

    def test_password_debil_falla(self, client):
        r = client.post("/auth/register", json={
            "email": "debil@test.com",
            "password": "123456",
        })
        assert r.status_code == 422

    def test_email_invalido_falla(self, client):
        r = client.post("/auth/register", json={
            "email": "no-es-email",
            "password": "Test@1234",
        })
        assert r.status_code == 422


class TestLogin:
    def test_login_exitoso(self, client, aprendiz):
        r = client.post("/auth/login", data={
            "username": aprendiz.email,
            "password": "Test@1234",
        })
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["rol"] == "APRENDIZ"

    def test_login_password_incorrecto(self, client, aprendiz):
        r = client.post("/auth/login", data={
            "username": aprendiz.email,
            "password": "Wrong@9999",
        })
        assert r.status_code == 401

    def test_login_usuario_inexistente(self, client):
        r = client.post("/auth/login", data={
            "username": "noexiste@test.com",
            "password": "Test@1234",
        })
        assert r.status_code == 401

    def test_login_tutor_pendiente_falla(self, client, db):
        tutor = make_usuario(db, rol=RolEnum.TUTOR, estado=EstadoUsuario.PENDIENTE)
        r = client.post("/auth/login", data={
            "username": tutor.email,
            "password": "Test@1234",
        })
        assert r.status_code == 403
        assert "pendiente" in r.json()["detail"].lower()

    def test_login_aprendiz_cohorte_finalizada_bloqueado(self, client, db):
        from backend.models.enums import EstadoCohorte
        from backend.tests.conftest import make_cohorte, make_perfil
        aprendiz = make_usuario(db, rol=RolEnum.APRENDIZ)
        tutor = make_usuario(db, rol=RolEnum.TUTOR)
        cohorte = make_cohorte(db, estado=EstadoCohorte.FINALIZADA, permitir_extension=False)
        make_perfil(db, aprendiz, cohorte, tutor)

        r = client.post("/auth/login", data={
            "username": aprendiz.email,
            "password": "Test@1234",
        })
        assert r.status_code == 403
        assert "finalizada" in r.json()["detail"].lower()

    def test_login_aprendiz_cohorte_finalizada_con_extension_permitida(self, client, db):
        from backend.models.enums import EstadoCohorte
        from backend.tests.conftest import make_cohorte, make_perfil
        aprendiz = make_usuario(db, rol=RolEnum.APRENDIZ)
        tutor = make_usuario(db, rol=RolEnum.TUTOR)
        cohorte = make_cohorte(db, estado=EstadoCohorte.FINALIZADA, permitir_extension=True)
        make_perfil(db, aprendiz, cohorte, tutor)

        r = client.post("/auth/login", data={
            "username": aprendiz.email,
            "password": "Test@1234",
        })
        assert r.status_code == 200


class TestMe:
    def test_me_autenticado(self, client, aprendiz):
        r = client.get("/auth/me", headers=auth_headers(aprendiz))
        assert r.status_code == 200
        assert r.json()["email"] == aprendiz.email

    def test_me_sin_token_falla(self, client):
        r = client.get("/auth/me")
        assert r.status_code == 401

    def test_me_token_invalido_falla(self, client):
        r = client.get("/auth/me", headers={"Authorization": "Bearer token.invalido"})
        assert r.status_code == 401
