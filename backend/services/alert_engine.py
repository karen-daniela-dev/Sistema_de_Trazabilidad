"""
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

# ── Umbrales ──────────────────────────────────────────────────────────────────
DIAS_INACTIVIDAD_YELLOW = 7
DIAS_INACTIVIDAD_RED = 14
APPS_SIN_ENTREVISTA_UMBRAL = 5
AVANCE_COHORTE_RIESGO = 0.70


# ── Semáforos ─────────────────────────────────────────────────────────────────

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
