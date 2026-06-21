"""
Router de aplicaciones.
El estado es calculado automáticamente — nunca aceptado del cliente.
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies.auth import get_current_user, require_any, require_aprendiz
from backend.middleware.audit_middleware import registrar
from backend.models.aplicacion import Aplicacion
from backend.models.aprendiz_perfil import AprendizPerfil
from backend.models.cohorte import Cohorte
from backend.models.usuario import Usuario
from backend.models.enums import RolEnum, EstadoCohorte
from backend.schemas import AplicacionCreate, AplicacionResponse, MarcarContratadoRequest
from backend.services.state_engine import marcar_contratado
from backend.utils.pagination import PaginationParams, Page

router = APIRouter(prefix="/aplicaciones", tags=["Aplicaciones"])


def _verificar_cohorte_activa(db: Session, usuario: Usuario) -> None:
    """Lanza 403 si la cohorte del aprendiz no está activa."""
    if usuario.rol != RolEnum.APRENDIZ:
        return
    perfil = db.query(AprendizPerfil).filter(AprendizPerfil.usuario_id == usuario.id).first()
    if not perfil:
        raise HTTPException(status_code=400, detail="Debes completar tu perfil primero.")
    cohorte: Cohorte = perfil.cohorte
    if not cohorte or cohorte.estado != EstadoCohorte.ACTIVA:
        raise HTTPException(
            status_code=403,
            detail="No puedes registrar aplicaciones. La cohorte no está activa.",
        )


@router.get("/", response_model=Page[AplicacionResponse])
def listar_aplicaciones(
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any),
):
    """
    - APRENDIZ: solo sus aplicaciones.
    - TUTOR: aplicaciones de sus aprendices.
    - COORDINADOR: todas.
    """
    query = db.query(Aplicacion)

    if current_user.rol == RolEnum.APRENDIZ:
        query = query.filter(Aplicacion.usuario_id == current_user.id)
    elif current_user.rol == RolEnum.TUTOR:
        aprendices_ids = [
            p.usuario_id for p in
            db.query(AprendizPerfil).filter(AprendizPerfil.tutor_id == current_user.id).all()
        ]
        query = query.filter(Aplicacion.usuario_id.in_(aprendices_ids))

    total = query.count()
    items = (
        query.order_by(Aplicacion.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.size)
        .all()
    )
    return Page.build(items, total, pagination)


@router.get("/{app_id}", response_model=AplicacionResponse)
def obtener_aplicacion(
    app_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any),
):
    app = db.query(Aplicacion).filter(Aplicacion.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Aplicación no encontrada.")
    # Aprendiz solo puede ver las suyas
    if current_user.rol == RolEnum.APRENDIZ and app.usuario_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sin permisos.")
    return app


@router.post("/", response_model=AplicacionResponse, status_code=201)
def crear_aplicacion(
    payload: AplicacionCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_aprendiz),
):
    _verificar_cohorte_activa(db, current_user)

    app = Aplicacion(
        usuario_id=current_user.id,
        empresa=payload.empresa,
        vacante=payload.vacante,
        modalidad=payload.modalidad,
        link=payload.link,
        fecha_aplicacion=payload.fecha_aplicacion,
        origen=payload.origen,
        # estado se inicia en APLICADO por defecto (model default)
    )
    db.add(app)
    db.flush()
    registrar(db, "CREATE_APLICACION", usuario_id=current_user.id,
              detalle={"empresa": payload.empresa, "vacante": payload.vacante},
              ip=request.headers.get("x-forwarded-for", request.client.host))
    db.commit()
    db.refresh(app)
    return app


@router.post("/marcar-contratado", response_model=AplicacionResponse)
def marcar_como_contratado(
    payload: MarcarContratadoRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_aprendiz),
):
    app = db.query(Aplicacion).filter(
        Aplicacion.id == payload.aplicacion_id,
        Aplicacion.usuario_id == current_user.id,
    ).first()
    if not app:
        raise HTTPException(status_code=404, detail="Aplicación no encontrada.")
    marcar_contratado(app)
    registrar(db, "MARCAR_CONTRATADO", usuario_id=current_user.id,
              detalle={"aplicacion_id": str(app.id)},
              ip=request.headers.get("x-forwarded-for", request.client.host))
    db.commit()
    db.refresh(app)
    return app


@router.delete("/{app_id}", status_code=204)
def eliminar_aplicacion(
    app_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_aprendiz),
):
    app = db.query(Aplicacion).filter(
        Aplicacion.id == app_id,
        Aplicacion.usuario_id == current_user.id,
    ).first()
    if not app:
        raise HTTPException(status_code=404, detail="Aplicación no encontrada.")
    registrar(db, "DELETE_APLICACION", usuario_id=current_user.id,
              detalle={"empresa": app.empresa, "vacante": app.vacante},
              ip=request.headers.get("x-forwarded-for", request.client.host))
    db.delete(app)
    db.commit()
