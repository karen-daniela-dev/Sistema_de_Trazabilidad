from __future__ import annotations

from collections import defaultdict
from typing import Iterable
from uuid import UUID

from sqlalchemy.orm import Session, selectinload

from backend.models.aplicacion import Aplicacion
from backend.models.entrevista import Entrevista
from backend.models.enums import EstadoApp
from backend.services.alert_engine import semaforo_actividad, semaforo_progreso
#bakend/services/kpi_helpers.y

def load_apps_and_entrevistas_for_users(
    db: Session,
    user_ids: Iterable[UUID] | None = None,
) -> tuple[defaultdict[UUID, list[Aplicacion]], defaultdict[UUID, list[Entrevista]]]:
    """Carga aplicaciones y entrevistas de uno o varios usuarios en pocas consultas."""
    if user_ids is None:
        apps = db.query(Aplicacion).options(selectinload(Aplicacion.entrevistas)).all()
    else:
        ids = list(user_ids)
        if not ids:
            return defaultdict(list), defaultdict(list)
        apps = (
            db.query(Aplicacion)
            .options(selectinload(Aplicacion.entrevistas))
            .filter(Aplicacion.usuario_id.in_(ids))
            .all()
        )

    apps_by_user: defaultdict[UUID, list[Aplicacion]] = defaultdict(list)
    entrevistas_by_app: defaultdict[UUID, list[Entrevista]] = defaultdict(list)

    for app in apps:
        apps_by_user[app.usuario_id].append(app)
        for entrevista in app.entrevistas:
            entrevistas_by_app[entrevista.aplicacion_id].append(entrevista)

    return apps_by_user, entrevistas_by_app


def collect_user_entrevistas(user_apps: list[Aplicacion], entrevistas_by_app) -> list[Entrevista]:
    """Agrupa entrevistas de las aplicaciones de un usuario."""
    entrevistas: list[Entrevista] = []
    for app in user_apps:
        entrevistas.extend(entrevistas_by_app.get(app.id, []))
    return entrevistas


def build_user_kpi(user_apps: list[Aplicacion], entrevistas: list[Entrevista]) -> dict:
    """Construye un resumen KPI para un usuario a partir de sus aplicaciones y entrevistas."""
    total_apps = len(user_apps)
    total_entrevistas = len(entrevistas)
    contratado = any(app.estado == EstadoApp.CONTRATADO for app in user_apps)
    conversion = round(total_entrevistas / total_apps, 2) if total_apps else 0.0

    fallas: dict[str, int] = {}
    for entrevista in entrevistas:
        for falla in entrevista.fallas or []:
            fallas[falla] = fallas.get(falla, 0) + 1

    return {
        "total_aplicaciones": total_apps,
        "total_entrevistas": total_entrevistas,
        "tasa_conversion": conversion,
        "contratado": contratado,
        "fallas_frecuentes": sorted(fallas.items(), key=lambda item: -item[1])[:5],
        "semaforo_actividad": semaforo_actividad(user_apps, entrevistas),
        "semaforo_progreso": semaforo_progreso(user_apps, entrevistas),
        "por_estado": {
            estado.value: sum(1 for app in user_apps if app.estado == estado)
            for estado in EstadoApp
        },
    }


def empty_summary() -> dict:
    return {
        "actividad": {"GREEN": 0, "YELLOW": 0, "RED": 0},
        "progreso": {"GREEN": 0, "YELLOW": 0, "RED": 0, "INSUFFICIENT_DATA": 0},
        "contratados": 0,
    }


def merge_summary(summary: dict, kpi: dict) -> None:
    summary["actividad"][kpi["semaforo_actividad"]] += 1
    summary["progreso"][kpi["semaforo_progreso"]] += 1
    if kpi["contratado"]:
        summary["contratados"] += 1
