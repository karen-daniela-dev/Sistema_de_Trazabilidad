"""
Tests unitarios — Motores de alertas, semáforos y ciclo de vida de cohorte.
"""
from datetime import date, datetime, timedelta, timezone
from unittest.mock import MagicMock

from backend.services.alert_engine import semaforo_aprendiz, semaforo_cohorte
from backend.services.cohort_engine import calcular_estado_cohorte, fecha_fin_desde_inicio
from backend.models.enums import EstadoApp, EstadoCohorte


# ── Semáforo Aprendiz ─────────────────────────────────────────────────────────

def make_app_mock(estado=EstadoApp.APLICADO, n_entrevistas=0):
    app = MagicMock()
    app.estado = estado
    app.entrevistas = [MagicMock() for _ in range(n_entrevistas)]
    return app


class TestSemaforoAprendiz:
    def test_sin_last_login_es_rojo(self):
        assert semaforo_aprendiz([], [], None) == "RED"

    def test_activo_recientemente_con_progreso_es_verde(self):
        app = make_app_mock(EstadoApp.AVANZANDO, n_entrevistas=2)
        last_login = datetime.now(timezone.utc) - timedelta(days=2)
        assert semaforo_aprendiz([app], [MagicMock(), MagicMock()], last_login) == "GREEN"

    def test_inactivo_14_dias_es_rojo(self):
        app = make_app_mock(n_entrevistas=1)
        last_login = datetime.now(timezone.utc) - timedelta(days=14)
        assert semaforo_aprendiz([app], [MagicMock()], last_login) == "RED"

    def test_inactivo_8_dias_es_amarillo(self):
        app = make_app_mock(n_entrevistas=1)
        last_login = datetime.now(timezone.utc) - timedelta(days=8)
        assert semaforo_aprendiz([app], [MagicMock()], last_login) == "YELLOW"

    def test_sin_entrevistas_es_amarillo(self):
        app = make_app_mock(n_entrevistas=0)
        last_login = datetime.now(timezone.utc) - timedelta(days=1)
        assert semaforo_aprendiz([app], [], last_login) == "YELLOW"

    def test_muchas_apps_sin_entrevistas_es_amarillo(self):
        apps = [make_app_mock(n_entrevistas=0) for _ in range(6)]
        last_login = datetime.now(timezone.utc) - timedelta(days=1)
        assert semaforo_aprendiz(apps, [], last_login) == "YELLOW"


# ── Semáforo Cohorte ──────────────────────────────────────────────────────────

def make_cohorte_mock(dias_inicio=-150, dias_fin=30, meta=10):
    c = MagicMock()
    hoy = date.today()
    c.fecha_inicio = hoy + timedelta(days=dias_inicio)
    c.fecha_fin = hoy + timedelta(days=dias_fin)
    c.meta_contratacion = meta
    return c


class TestSemaforoCohorte:
    def test_cohorte_en_buen_camino_es_verde(self):
        c = make_cohorte_mock(dias_inicio=-30, dias_fin=150, meta=10)
        assert semaforo_cohorte(c, contratados=3) == "GREEN"

    def test_cohorte_al_70_pct_con_mitad_contratados_es_amarillo(self):
        # 70% de 180 días = 126 días transcurridos
        c = make_cohorte_mock(dias_inicio=-126, dias_fin=54, meta=10)
        assert semaforo_cohorte(c, contratados=6) == "YELLOW"

    def test_cohorte_al_70_pct_sin_contratados_es_rojo(self):
        c = make_cohorte_mock(dias_inicio=-126, dias_fin=54, meta=10)
        assert semaforo_cohorte(c, contratados=2) == "RED"

    def test_meta_cumplida_es_verde(self):
        c = make_cohorte_mock(dias_inicio=-160, dias_fin=20, meta=10)
        assert semaforo_cohorte(c, contratados=10) == "GREEN"


# ── Cohort Engine ─────────────────────────────────────────────────────────────

class TestCohortEngine:
    def test_fecha_fin_6_meses(self):
        inicio = date(2024, 1, 15)
        fin = fecha_fin_desde_inicio(inicio)
        assert fin == date(2024, 7, 15)

    def test_fecha_fin_cruce_de_ano(self):
        inicio = date(2024, 10, 1)
        fin = fecha_fin_desde_inicio(inicio)
        assert fin == date(2025, 4, 1)

    def test_estado_activa_antes_de_fin(self):
        c = MagicMock()
        c.fecha_inicio = date.today() - timedelta(days=30)
        c.fecha_fin = date.today() + timedelta(days=150)
        assert calcular_estado_cohorte(c) == EstadoCohorte.ACTIVA

    def test_estado_finalizada_en_fecha_fin(self):
        c = MagicMock()
        c.fecha_inicio = date.today() - timedelta(days=180)
        c.fecha_fin = date.today() - timedelta(days=1)
        assert calcular_estado_cohorte(c) == EstadoCohorte.FINALIZADA

    def test_estado_inactiva_despues_de_30_dias(self):
        c = MagicMock()
        c.fecha_inicio = date.today() - timedelta(days=220)
        c.fecha_fin = date.today() - timedelta(days=40)
        assert calcular_estado_cohorte(c) == EstadoCohorte.INACTIVA
