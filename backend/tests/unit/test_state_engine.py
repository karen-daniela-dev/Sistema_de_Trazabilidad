"""
Tests unitarios — Motor de estados de aplicación.
No requieren BD — solo lógica pura.
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from backend.models.enums import EstadoApp
from backend.services.state_engine import calcular_estado, aplicar_estado, marcar_contratado


def make_app(estado=EstadoApp.APLICADO):
    app = MagicMock()
    app.estado = estado
    return app


def make_entrevista(dias_atras=0):
    e = MagicMock()
    e.fecha = datetime.now(timezone.utc) - timedelta(days=dias_atras)
    return e


class TestCalcularEstado:
    def test_sin_entrevistas_es_aplicado(self):
        app = make_app()
        assert calcular_estado(app, []) == EstadoApp.APLICADO

    def test_una_entrevista_es_en_espera(self):
        app = make_app()
        assert calcular_estado(app, [make_entrevista()]) == EstadoApp.EN_ESPERA

    def test_dos_entrevistas_recientes_es_avanzando(self):
        app = make_app()
        entrevistas = [make_entrevista(1), make_entrevista(3)]
        assert calcular_estado(app, entrevistas) == EstadoApp.AVANZANDO

    def test_dos_entrevistas_10_dias_es_rechazado(self):
        app = make_app()
        entrevistas = [make_entrevista(20), make_entrevista(10)]
        assert calcular_estado(app, entrevistas) == EstadoApp.RECHAZADO

    def test_dos_entrevistas_15_dias_es_rechazado(self):
        app = make_app()
        entrevistas = [make_entrevista(20), make_entrevista(15)]
        assert calcular_estado(app, entrevistas) == EstadoApp.RECHAZADO

    def test_9_dias_no_rechaza(self):
        """Justo antes del umbral — debe ser AVANZANDO."""
        app = make_app()
        entrevistas = [make_entrevista(20), make_entrevista(9)]
        assert calcular_estado(app, entrevistas) == EstadoApp.AVANZANDO

    def test_16_dias_no_rechaza(self):
        """Pasado el umbral máximo — no aplica RECHAZADO."""
        app = make_app()
        entrevistas = [make_entrevista(20), make_entrevista(16)]
        assert calcular_estado(app, entrevistas) == EstadoApp.AVANZANDO

    def test_contratado_es_terminal(self):
        """CONTRATADO nunca se sobreescribe."""
        app = make_app(EstadoApp.CONTRATADO)
        entrevistas = [make_entrevista(12), make_entrevista(12)]  # debería ser RECHAZADO
        assert calcular_estado(app, entrevistas) == EstadoApp.CONTRATADO

    def test_rechazado_con_nueva_entrevista_avanza(self):
        """Si estaba RECHAZADO y hay nueva entrevista reciente → AVANZANDO."""
        app = make_app(EstadoApp.RECHAZADO)
        entrevistas = [make_entrevista(20), make_entrevista(12), make_entrevista(1)]
        # 3 entrevistas, última hace 1 día → AVANZANDO
        assert calcular_estado(app, entrevistas) == EstadoApp.AVANZANDO

    def test_mas_de_dos_entrevistas_recientes_es_avanzando(self):
        app = make_app()
        entrevistas = [make_entrevista(30), make_entrevista(20), make_entrevista(2)]
        assert calcular_estado(app, entrevistas) == EstadoApp.AVANZANDO


class TestAplicarEstado:
    def test_actualiza_estado_cuando_cambia(self):
        app = make_app(EstadoApp.APLICADO)
        cambio = aplicar_estado(app, [make_entrevista()])
        assert cambio is True
        assert app.estado == EstadoApp.EN_ESPERA

    def test_no_actualiza_si_mismo_estado(self):
        app = make_app(EstadoApp.APLICADO)
        cambio = aplicar_estado(app, [])
        assert cambio is False

    def test_no_cambia_contratado(self):
        app = make_app(EstadoApp.CONTRATADO)
        cambio = aplicar_estado(app, [make_entrevista(12), make_entrevista(12)])
        assert cambio is False
        assert app.estado == EstadoApp.CONTRATADO


class TestMarcarContratado:
    def test_marca_contratado(self):
        app = make_app(EstadoApp.AVANZANDO)
        marcar_contratado(app)
        assert app.estado == EstadoApp.CONTRATADO

    def test_puede_marcar_desde_cualquier_estado(self):
        for estado in [EstadoApp.APLICADO, EstadoApp.EN_ESPERA, EstadoApp.RECHAZADO]:
            app = make_app(estado)
            marcar_contratado(app)
            assert app.estado == EstadoApp.CONTRATADO
