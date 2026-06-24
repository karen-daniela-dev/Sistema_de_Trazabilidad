"""
services/alert_engine.py
Motor de alertas y semáforos.
Detecta patrones de inactividad, baja conversión y riesgo de cohorte.
"""
from datetime import date, datetime
from typing import Sequence

from sqlalchemy.orm import Session

from backend.models.alerta import Alerta
from backend.models.aplicacion import Aplicacion
from backend.models.cohorte import Cohorte
from backend.models.entrevista import Entrevista
from backend.models.usuario import Usuario
from backend.models.enums import EstadoApp
from backend.services.state_engine import _dias_desde

# ── Umbrales ──────────────────────────────────────────────────────────────────
DIAS_INACTIVIDAD_YELLOW = 7
DIAS_INACTIVIDAD_RED = 14

DIAS_GRACIA_PROGRESO = 8
CONVERSION_GREEN = 0.25
CONVERSION_YELLOW = 0.10


APPS_SIN_ENTREVISTA_UMBRAL = 5
AVANCE_COHORTE_RIESGO = 0.70


# ── Semáforos ─────────────────────────────────────────────────────────────────
#deprecado
def semaforo_aprendiz(
    aplicaciones: Sequence[Aplicacion],
    entrevistas: Sequence[Entrevista],
    last_login: datetime | None,
) -> str:
    """Retorna 'GREEN', 'YELLOW' o 'RED'."""
    if not last_login:
        return "RED"

    last = last_login.date() if hasattr(last_login, "date") else last_login
    dias_inactivo = (date.today() - last).days

    if dias_inactivo >= DIAS_INACTIVIDAD_RED:
        return "RED"

    tiene_entrevistas = len(entrevistas) > 0
    tiene_progreso = any(
        a.estado in (EstadoApp.AVANZANDO, EstadoApp.CONTRATADO) for a in aplicaciones
    )
    apps_sin_entrevista = sum(1 for a in aplicaciones if len(a.entrevistas) == 0)

    if (
        dias_inactivo >= DIAS_INACTIVIDAD_YELLOW
        or not tiene_entrevistas
        or apps_sin_entrevista >= APPS_SIN_ENTREVISTA_UMBRAL
    ):
        return "YELLOW"

    return "GREEN"






def semaforo_actividad(
    aplicaciones: Sequence[Aplicacion],
    entrevistas: Sequence[Entrevista],
) -> str:
    """
    Evalúa actividad real del aprendiz.
    Señal principal: aplicaciones.
    Señal secundaria: entrevistas.
    """

    if not aplicaciones:
        return "RED"

    if any(a.estado == EstadoApp.CONTRATADO for a in aplicaciones):
        return "GREEN"

    fechas = [a.fecha_aplicacion for a in aplicaciones]

    if entrevistas:
        fechas.extend(
            e.fecha.date() if hasattr(e.fecha, "date") else e.fecha
            for e in entrevistas
        )
    ultima_actividad = max(fechas)
    dias = _dias_desde(ultima_actividad)

    if dias > DIAS_INACTIVIDAD_RED:
        return "RED"

    if dias >= DIAS_INACTIVIDAD_YELLOW:
        return "YELLOW"

    return "GREEN"


def semaforo_progreso(
    aplicaciones: Sequence[Aplicacion],
    entrevistas: Sequence[Entrevista],
) -> str:
    """
    Evalúa progreso real del proceso de empleabilidad.
    Basado en aplicaciones maduras + conversión + estados.
    """

    if not aplicaciones:
        return "INSUFFICIENT_DATA"

    if any(a.estado == EstadoApp.CONTRATADO for a in aplicaciones):
        return "GREEN"

    hoy = date.today()

    apps_maduras = [
        a for a in aplicaciones
        if (hoy - a.fecha_aplicacion).days >= DIAS_GRACIA_PROGRESO
    ]

    if len(apps_maduras) < 5:
        return "INSUFFICIENT_DATA"

    apps_con_entrevista = sum(
        1 for a in apps_maduras if len(a.entrevistas) > 0
    )

    conversion = apps_con_entrevista / len(apps_maduras)

    apps_espera = sum(
        1 for a in apps_maduras if a.estado == EstadoApp.EN_ESPERA
    )

    apps_avanzando = sum(
        1 for a in apps_maduras if a.estado == EstadoApp.AVANZANDO
    )

    score = 0

    # Conversión
    if conversion >= CONVERSION_GREEN:
        score += 50
    elif conversion >= CONVERSION_YELLOW:
        score += 25

    # Estados
    score += apps_espera * 10
    score += apps_avanzando * 20

    if score >= 60:
        return "GREEN"

    if score >= 25:
        return "YELLOW"

    return "RED"





def semaforo_cohorte(cohorte: Cohorte, contratados: int) -> str:
    """Retorna 'GREEN', 'YELLOW' o 'RED' para una cohorte."""
    hoy = date.today()
    total_dias = (cohorte.fecha_fin - cohorte.fecha_inicio).days
    if total_dias <= 0:
        return "RED"
    transcurridos = (hoy - cohorte.fecha_inicio).days
    avance = min(transcurridos / total_dias, 1.0)

    if avance >= AVANCE_COHORTE_RIESGO and contratados < cohorte.meta_contratacion * 0.5:
        return "RED"
    if avance >= AVANCE_COHORTE_RIESGO and contratados < cohorte.meta_contratacion:
        return "YELLOW"
    return "GREEN"


# ── Generación de alertas ─────────────────────────────────────────────────────

def _crear_alerta(
    db: Session, tipo: str, mensaje: str, target_id, target_type: str
) -> Alerta:
    alerta = Alerta(
        tipo=tipo,
        mensaje=mensaje,
        target_id=target_id,
        target_type=target_type,
    )
    db.add(alerta)
    return alerta


def evaluar_alertas_aprendiz(
    db: Session,
    usuario: Usuario,
    aplicaciones: Sequence[Aplicacion],
    entrevistas: Sequence[Entrevista],
) -> list[Alerta]:
    """Genera y persiste alertas para un aprendiz según su actividad."""
    alertas = []
    semaforo = semaforo_aprendiz(aplicaciones, entrevistas, usuario.last_login)

    if semaforo == "RED":
        alertas.append(_crear_alerta(
            db, "INACTIVIDAD",
            f"El aprendiz {usuario.email} lleva más de {DIAS_INACTIVIDAD_RED} días sin actividad.",
            usuario.id, "APRENDIZ",
        ))

    apps_sin_entrevista = sum(1 for a in aplicaciones if len(a.entrevistas) == 0)
    if apps_sin_entrevista >= APPS_SIN_ENTREVISTA_UMBRAL:
        alertas.append(_crear_alerta(
            db, "BAJA_CONVERSION",
            f"{apps_sin_entrevista} aplicaciones sin ninguna entrevista.",
            usuario.id, "APRENDIZ",
        ))

    rechazados = [a for a in aplicaciones if a.estado == EstadoApp.RECHAZADO]
    if len(rechazados) >= 3:
        alertas.append(_crear_alerta(
            db, "MULTIPLES_RECHAZOS",
            f"El aprendiz tiene {len(rechazados)} aplicaciones rechazadas.",
            usuario.id, "APRENDIZ",
        ))

    db.flush()
    return alertas


def evaluar_alertas_cohorte(db: Session, cohorte: Cohorte, contratados: int) -> list[Alerta]:
    alertas = []
    semaforo = semaforo_cohorte(cohorte, contratados)

    if semaforo in ("RED", "YELLOW"):
        alertas.append(_crear_alerta(
            db, f"COHORTE_{semaforo}",
            f"Cohorte '{cohorte.nombre}': {contratados}/{cohorte.meta_contratacion} contratados. Semáforo {semaforo}.",
            cohorte.id, "COHORTE",
        ))
    db.flush()
    return alertas
