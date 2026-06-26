"""
routes/kpis.py
Router de KPIs — datos por rol.
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies.auth import (
    get_current_user, require_coordinador, require_tutor, require_aprendiz, require_any
)
from backend.models.usuario import Usuario
from backend.models.enums import RolEnum
from backend.services import kpi_service, alert_engine
from backend.models.aprendiz_perfil import AprendizPerfil
from backend.models.alerta import Alerta
from backend.models.cohorte import Cohorte
from backend.schemas import AlertaResponse
from backend.services.query_service import get_tutor_aprendiz_ids

router = APIRouter(prefix="/kpis", tags=["KPIs y Dashboards"])


@router.get("/personal")
def kpis_personales(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_aprendiz),
):
    return kpi_service.kpis_personales(db, current_user.id)


@router.get("/grupo")
def kpis_grupo(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_tutor),
):
    if current_user.rol == RolEnum.COORDINADOR:
        # Coordinador puede ver el resumen general
        return kpi_service.kpis_globales(db)
    return kpi_service.kpis_grupo(db, current_user.id)


@router.get("/global")
def kpis_globales(
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_coordinador),
):
    return kpi_service.kpis_globales(db)


@router.get("/alertas", response_model=list[AlertaResponse])
def mis_alertas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any),
):
    """
    Retorna alertas no leídas relevantes para el usuario actual.
    """
    query = db.query(Alerta).filter(Alerta.leida == False)

    if current_user.rol == RolEnum.APRENDIZ:
        query = query.filter(
            Alerta.target_id == current_user.id,
            Alerta.target_type == "APRENDIZ",
        )
    elif current_user.rol == RolEnum.TUTOR:
        aprendices_ids = get_tutor_aprendiz_ids(db, current_user.id)
        query = query.filter(
            Alerta.target_id.in_([current_user.id] + aprendices_ids)
        )
    # Coordinador ve todas

    rows = query.order_by(Alerta.created_at.desc()).limit(50).all()
    return [
        AlertaResponse(
            id=row.id,
            target_id=row.target_id,
            target_type=row.target_type,
            mensaje=row.mensaje,
            leida=row.leida,
            created_at=row.created_at,
        )
        for row in rows
    ]


@router.patch("/alertas/{alerta_id}/leer", status_code=200)
def marcar_alerta_leida(
    alerta_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_any),
):
    alerta = db.query(Alerta).filter(Alerta.id == alerta_id).first()
    if not alerta:
        raise HTTPException(status_code=404, detail="Alerta no encontrada.")
    alerta.leida = True
    db.commit()
    return {"message": "Alerta marcada como leída."}

@router.get("/cohortes")
def kpis_cohortes(
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_coordinador),
):
    return kpi_service.kpis_cohortes(db)

@router.get("/cohorte/{cohorte_id}")
def kpis_cohorte_detalle(
    cohorte_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_coordinador),
):
    return kpi_service.kpis_detalle_cohorte(db, cohorte_id)


@router.get("/cohorte/{cohorte_id}/tutores")
def kpis_tutores_por_cohorte(
    cohorte_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_coordinador),
):
    """
    Ranking únicamente de los tutores pertenecientes
    a una cohorte.
    """
    return kpi_service.kpis_tutores_por_cohorte(
        db,
        cohorte_id,
    )

@router.get("/tutores")
def kpis_tutores(
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_coordinador),
):
    return kpi_service.kpis_tutores(db)

@router.get("/tutores/{tutor_id}")
def detalle_tutor(
    tutor_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_coordinador),
):
    return kpi_service.kpis_grupo(db, tutor_id)

@router.get("/cohorte/{cohorte_id}/tutores/{tutor_id}")
def detalle_tutor_cohorte(
    cohorte_id: uuid.UUID,
    tutor_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_coordinador),
):
    """
    Devuelve únicamente los aprendices
    del tutor dentro de una cohorte.
    """
    return kpi_service.kpis_tutor_cohorte(
        db,
        cohorte_id,
        tutor_id,
    )