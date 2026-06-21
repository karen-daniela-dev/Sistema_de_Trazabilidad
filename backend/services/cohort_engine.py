"""
Motor de ciclo de vida de cohortes.
Transiciona estados ACTIVA → FINALIZADA → INACTIVA automáticamente.
"""
from datetime import date, timedelta

from sqlalchemy.orm import Session

from backend.models.cohorte import Cohorte
from backend.models.enums import EstadoCohorte

DIAS_HASTA_INACTIVA = 30  # días tras FINALIZADA para pasar a INACTIVA


def calcular_estado_cohorte(cohorte: Cohorte) -> EstadoCohorte:
    hoy = date.today()
    if hoy < cohorte.fecha_fin:
        return EstadoCohorte.ACTIVA
    if hoy >= cohorte.fecha_fin + timedelta(days=DIAS_HASTA_INACTIVA):
        return EstadoCohorte.INACTIVA
    return EstadoCohorte.FINALIZADA


def sincronizar_estados_cohortes(db: Session) -> int:
    """
    Ejecutar periódicamente (cron / startup).
    Retorna el número de cohortes actualizadas.
    """
    cohortes = db.query(Cohorte).filter(
        Cohorte.estado != EstadoCohorte.INACTIVA
    ).all()
    actualizadas = 0
    for c in cohortes:
        nuevo = calcular_estado_cohorte(c)
        if c.estado != nuevo:
            c.estado = nuevo
            actualizadas += 1
    if actualizadas:
        db.commit()
    return actualizadas


def fecha_fin_desde_inicio(inicio: date) -> date:
    """Calcula fecha_fin = fecha_inicio + 6 meses."""
    mes = inicio.month + 6
    anio = inicio.year + (mes - 1) // 12
    mes = (mes - 1) % 12 + 1
    return inicio.replace(year=anio, month=mes)
