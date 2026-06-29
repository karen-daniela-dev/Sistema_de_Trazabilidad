"""
Tests de integración — Entrevistas y validaciones condicionales.
"""
from datetime import datetime, timezone, timedelta
from backend.tests.conftest import auth_headers


def _now_iso(dias_atras=0):
    return (datetime.now(timezone.utc) - timedelta(days=dias_atras)).isoformat()


def crear_app(client, headers):
    r = client.post("/aplicaciones/", json={
        "empresa": "Empresa Test",
        "vacante": "Dev",
        "modalidad": "REMOTO",
        "origen": "PROPIA",
    }, headers=headers)
    assert r.status_code == 201
    return r.json()["id"]


class TestCrearEntrevista:
    def test_entrevista_basica_exitosa(self, client, setup_aprendiz_completo):
        aprendiz, *_ = setup_aprendiz_completo
        h = auth_headers(aprendiz)
        app_id = crear_app(client, h)
        r = client.post("/entrevistas/", json={
            "aplicacion_id": app_id,
            "tipo": "RRHH",
            "modalidad": "VIRTUAL",
            "fecha": _now_iso(1),
            "grupal": False,
        }, headers=h)
        assert r.status_code == 201
        data = r.json()
        assert data["tipo"] == "RRHH"

    def test_grupal_sin_percepcion_falla(self, client, setup_aprendiz_completo):
        aprendiz, *_ = setup_aprendiz_completo
        h = auth_headers(aprendiz)
        app_id = crear_app(client, h)
        r = client.post("/entrevistas/", json={
            "aplicacion_id": app_id,
            "tipo": "TECNICA",
            "modalidad": "VIRTUAL",
            "fecha": _now_iso(1),
            "grupal": True,
            # percepcion_grupal omitida
        }, headers=h)
        assert r.status_code == 422
        body = r.json()
        assert "percepcion_grupal" in str(body).lower()

    def test_grupal_con_percepcion_exitoso(self, client, setup_aprendiz_completo):
        aprendiz, *_ = setup_aprendiz_completo
        h = auth_headers(aprendiz)
        app_id = crear_app(client, h)
        r = client.post("/entrevistas/", json={
            "aplicacion_id": app_id,
            "tipo": "TECNICA",
            "modalidad": "VIRTUAL",
            "fecha": _now_iso(1),
            "grupal": True,
            "percepcion_grupal": "MEJOR",
        }, headers=h)
        assert r.status_code == 201

    def test_temas_tecnicos_sin_falla_tecnica_falla(self, client, setup_aprendiz_completo):
        aprendiz, *_ = setup_aprendiz_completo
        h = auth_headers(aprendiz)
        app_id = crear_app(client, h)
        r = client.post("/entrevistas/", json={
            "aplicacion_id": app_id,
            "tipo": "TECNICA",
            "modalidad": "VIRTUAL",
            "fecha": _now_iso(1),
            "grupal": False,
            "fallas": ["COMUNICACION"],   # No TECNICA
            "temas_tecnicos": ["JAVA"],   # no debería estar sin falla TECNICA
        }, headers=h)
        assert r.status_code == 422

    def test_temas_tecnicos_con_falla_tecnica_exitoso(self, client, setup_aprendiz_completo):
        aprendiz, *_ = setup_aprendiz_completo
        h = auth_headers(aprendiz)
        app_id = crear_app(client, h)
        r = client.post("/entrevistas/", json={
            "aplicacion_id": app_id,
            "tipo": "TECNICA",
            "modalidad": "VIRTUAL",
            "fecha": _now_iso(1),
            "grupal": False,
            "fallas": ["TECNICA"],
            "temas_tecnicos": ["JAVA", "SQL"],
        }, headers=h)
        assert r.status_code == 201

    def test_autoevaluacion_fuera_de_rango_falla(self, client, setup_aprendiz_completo):
        aprendiz, *_ = setup_aprendiz_completo
        h = auth_headers(aprendiz)
        app_id = crear_app(client, h)
        r = client.post("/entrevistas/", json={
            "aplicacion_id": app_id,
            "tipo": "RRHH",
            "modalidad": "VIRTUAL",
            "fecha": _now_iso(1),
            "grupal": False,
            "autoevaluacion": 6,
        }, headers=h)
        assert r.status_code == 422

    def test_subfallas_invalidas_para_falla_falla(self, client, setup_aprendiz_completo):
        aprendiz, *_ = setup_aprendiz_completo
        h = auth_headers(aprendiz)
        app_id = crear_app(client, h)
        r = client.post("/entrevistas/", json={
            "aplicacion_id": app_id,
            "tipo": "RRHH",
            "modalidad": "VIRTUAL",
            "fecha": _now_iso(1),
            "grupal": False,
            "fallas": ["COMUNICACION"],
            "subfallas": ["JAVA_BASICO"],  # subfalla de TECNICA, no COMUNICACION
        }, headers=h)
        assert r.status_code == 422

    def test_entrevista_de_otro_aprendiz_falla(self, client, db, setup_aprendiz_completo):
        from backend.tests.conftest import make_usuario, make_perfil
        from backend.models.enums import RolEnum
        aprendiz, tutor, cohorte, _ = setup_aprendiz_completo
        aprendiz2 = make_usuario(db, rol=RolEnum.APRENDIZ)
        make_perfil(db, aprendiz2, cohorte, tutor)

        app_id = crear_app(client, auth_headers(aprendiz))
        r = client.post("/entrevistas/", json={
            "aplicacion_id": app_id,
            "tipo": "RRHH",
            "modalidad": "VIRTUAL",
            "fecha": _now_iso(1),
            "grupal": False,
        }, headers=auth_headers(aprendiz2))
        assert r.status_code == 404  # No ve la aplicación ajena


class TestListarEntrevistas:
    def test_listar_por_aplicacion(self, client, setup_aprendiz_completo):
        aprendiz, *_ = setup_aprendiz_completo
        h = auth_headers(aprendiz)
        app_id = crear_app(client, h)
        client.post("/entrevistas/", json={
            "aplicacion_id": app_id, "tipo": "RRHH",
            "modalidad": "VIRTUAL", "fecha": _now_iso(1), "grupal": False,
        }, headers=h)
        r = client.get(f"/entrevistas/por-aplicacion/{app_id}", headers=h)
        assert r.status_code == 200
        assert len(r.json()) == 1
