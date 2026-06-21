"""
Motor de estados de aplicación.
La lógica de transición vive SOLO aquí — nunca en routers ni modelos.
"""
from datetime import date, datetime, timezone
from typing import Sequence

from backend.models.aplicacion import Aplicacion
from backend.models.entrevista import Entrevista
from backend.models.enums import EstadoApp

# Días sin nueva entrevista para marcar RECHAZADO automáticamente
DIAS_RECHAZO_MIN = 10
DIAS_RECHAZO_MAX = 15


def _dias_desde(dt: datetime) -> int:
    """Días transcurridos desde una fecha/hora aware o naive."""
    hoy = date.today()
    if hasattr(dt, "date"):
        return (hoy - dt.date()).days
    return (hoy - dt).days


def calcular_estado(aplicacion: Aplicacion, entrevistas: Sequence[Entrevista]) -> EstadoApp:
    """
    Calcula el estado correcto según las reglas del sistema.
    NO modifica la aplicación — solo retorna el nuevo estado.

    Reglas:
    1. CONTRATADO es terminal — nunca se sobreescribe.
    2. 0 entrevistas → APLICADO
    3. 1 entrevista → EN_ESPERA
    4. ≥2 entrevistas:
       - Si days_since_last ∈ [10, 15] → RECHAZADO
       - Si estaba RECHAZADO y hay nueva entrevista → AVANZANDO
       - Caso base → AVANZANDO
    """
    if aplicacion.estado == EstadoApp.CONTRATADO:
        return EstadoApp.CONTRATADO

    n = len(entrevistas)

    if n == 0:
        return EstadoApp.APLICADO

    if n == 1:
        return EstadoApp.EN_ESPERA

    # n >= 2
    ultima = max(entrevistas, key=lambda e: e.fecha)
    dias = _dias_desde(ultima.fecha)

    if DIAS_RECHAZO_MIN <= dias <= DIAS_RECHAZO_MAX:
        return EstadoApp.RECHAZADO

    return EstadoApp.AVANZANDO


def aplicar_estado(aplicacion: Aplicacion, entrevistas: Sequence[Entrevista]) -> bool:
    """
    Calcula y aplica el estado a la aplicación.
    Retorna True si el estado cambió.
    """
    nuevo = calcular_estado(aplicacion, entrevistas)
    if aplicacion.estado != nuevo:
        aplicacion.estado = nuevo
        return True
    return False


def marcar_contratado(aplicacion: Aplicacion) -> None:
    """
    Único punto donde un APRENDIZ puede cambiar estado a CONTRATADO.
    """
    aplicacion.estado = EstadoApp.CONTRATADO
