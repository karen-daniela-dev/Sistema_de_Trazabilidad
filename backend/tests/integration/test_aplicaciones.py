"""
Tests de integración — Aplicaciones y flujo del motor de estados.
"""
from datetime import datetime, timezone, timedelta
from backend.tests.conftest import auth_headers, make_usuario, make_cohorte, make_perfil
from backend.models.enums import RolEnum, EstadoCohorte


def crear_aplicacion(client, headers, empresa="TechCorp", vacante="Backend Dev"):
    return client.post("/aplicaciones/", json={
        "empresa": empresa,
        "vacante": vacante,
        "modalidad": "REMOTO",
        "origen": "PROPIA",
        "fecha_aplicacion": "2024-06-01",
    }, headers=headers)


def crear_entrevista(client, headers, app_id, dias_atras=1):
    fecha = (datetime.now(timezone.utc) - timedelta(days=dias_atras)).isoformat()
    return client.post("/entrevistas/", json={
        "aplicacion_id": str(app_id),
        "tipo": "RRHH",
        "modalidad": "VIRTUAL",
        "fecha": fecha,
        "grupal": False,
        "fallas": [],
        "autoevaluacion": 4,
        "reflexion_bien": "Buena comunicación",
        "reflexion_mejorar": "Más preparación técnica",
    }, headers=headers)


class TestCrearAplicacion:
    def test_aprendiz_puede_crear(self, client, setup_aprendiz_completo):
        aprendiz, *_ = setup_aprendiz_completo
        r = crear_aplicacion(client, auth_headers(aprendiz))
        assert r.status_code == 201
        data = r.json()
        assert data["estado"] == "APLICADO"
        assert data["empresa"] == "TechCorp"

    def test_tutor_no_puede_crear(self, client, tutor):
        r = crear_aplicacion(client, auth_headers(tutor))
        assert r.status_code == 403

    def test_coordinador_no_puede_crear(self, client, coordinador):
        r = crear_aplicacion(client, auth_headers(coordinador))
        assert r.status_code == 403

    def test_aprendiz_sin_perfil_no_puede_crear(self, client, aprendiz):
        r = crear_aplicacion(client, auth_headers(aprendiz))
        assert r.status_code in (400, 403)

    def test_empresa_vacia_falla(self, client, setup_aprendiz_completo):
        aprendiz, *_ = setup_aprendiz_completo
        r = client.post("/aplicaciones/", json={
            "empresa": "   ",
            "vacante": "Dev",
            "modalidad": "REMOTO",
            "origen": "PROPIA",
        }, headers=auth_headers(aprendiz))
        assert r.status_code == 422

    def test_cohorte_finalizada_bloquea_crear(self, client, db):
        aprendiz = make_usuario(db, rol=RolEnum.APRENDIZ)
        tutor = make_usuario(db, rol=RolEnum.TUTOR)
        cohorte = make_cohorte(db, estado=EstadoCohorte.FINALIZADA)
        make_perfil(db, aprendiz, cohorte, tutor)
        r = crear_aplicacion(client, auth_headers(aprendiz))
        assert r.status_code == 403


class TestListarAplicaciones:
    def test_aprendiz_solo_ve_las_suyas(self, client, setup_aprendiz_completo, db):
        aprendiz, tutor, cohorte, _ = setup_aprendiz_completo
        aprendiz2 = make_usuario(db, rol=RolEnum.APRENDIZ)
        make_perfil(db, aprendiz2, cohorte, tutor)
        # Crear app para aprendiz2
        crear_aplicacion(client, auth_headers(aprendiz2), empresa="OtraEmpresa")
        # Crear app para aprendiz
        crear_aplicacion(client, auth_headers(aprendiz))
        r = client.get("/aplicaciones/", headers=auth_headers(aprendiz))
        assert r.status_code == 200
        empresas = [a["empresa"] for a in r.json()["items"]]
        assert "OtraEmpresa" not in empresas

    def test_coordinador_ve_todas(self, client, coordinador, setup_aprendiz_completo):
        aprendiz, *_ = setup_aprendiz_completo
        crear_aplicacion(client, auth_headers(aprendiz))
        r = client.get("/aplicaciones/", headers=auth_headers(coordinador))
        assert r.status_code == 200
        assert r.json()["total"] >= 1


class TestFlujoEstados:
    """Prueba el flujo completo de transiciones de estado."""

    def test_flujo_completo_aplicado_a_avanzando(self, client, setup_aprendiz_completo):
        aprendiz, *_ = setup_aprendiz_completo
        headers = auth_headers(aprendiz)

        # 1. Crear aplicación → APLICADO
        r = crear_aplicacion(client, headers)
        assert r.status_code == 201
        app_id = r.json()["id"]
        assert r.json()["estado"] == "APLICADO"

        # 2. Primera entrevista → EN_ESPERA
        r = crear_entrevista(client, headers, app_id, dias_atras=5)
        assert r.status_code == 201
        r = client.get(f"/aplicaciones/{app_id}", headers=headers)
        assert r.json()["estado"] == "EN_ESPERA"

        # 3. Segunda entrevista reciente → AVANZANDO
        r = crear_entrevista(client, headers, app_id, dias_atras=1)
        assert r.status_code == 201
        r = client.get(f"/aplicaciones/{app_id}", headers=headers)
        assert r.json()["estado"] == "AVANZANDO"

    def test_marcar_contratado(self, client, setup_aprendiz_completo):
        aprendiz, *_ = setup_aprendiz_completo
        headers = auth_headers(aprendiz)
        r = crear_aplicacion(client, headers)
        app_id = r.json()["id"]

        r = client.post("/aplicaciones/marcar-contratado",
                        json={"aplicacion_id": app_id}, headers=headers)
        assert r.status_code == 200
        assert r.json()["estado"] == "CONTRATADO"

    def test_contratado_no_regresa_a_otro_estado(self, client, setup_aprendiz_completo):
        aprendiz, *_ = setup_aprendiz_completo
        headers = auth_headers(aprendiz)
        r = crear_aplicacion(client, headers)
        app_id = r.json()["id"]

        client.post("/aplicaciones/marcar-contratado",
                    json={"aplicacion_id": app_id}, headers=headers)

        # Agregar entrevista "vieja" que debería causar RECHAZADO
        crear_entrevista(client, headers, app_id, dias_atras=12)
        crear_entrevista(client, headers, app_id, dias_atras=12)

        r = client.get(f"/aplicaciones/{app_id}", headers=headers)
        # CONTRATADO es terminal
        assert r.json()["estado"] == "CONTRATADO"

    def test_aprendiz_no_puede_ver_aplicacion_de_otro(self, client, db, setup_aprendiz_completo):
        aprendiz, tutor, cohorte, _ = setup_aprendiz_completo
        aprendiz2 = make_usuario(db, rol=RolEnum.APRENDIZ)
        make_perfil(db, aprendiz2, cohorte, tutor)

        r = crear_aplicacion(client, auth_headers(aprendiz2))
        app_id = r.json()["id"]

        r = client.get(f"/aplicaciones/{app_id}", headers=auth_headers(aprendiz))
        assert r.status_code == 403
