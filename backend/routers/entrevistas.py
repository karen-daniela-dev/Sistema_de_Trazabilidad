"""
Router de entrevistas.
Cada creación dispara el motor de estados sobre la aplicación padre.
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies.auth import get_current_user, require_any, require_aprendiz
from backend.middleware.audit_middleware import registrar
from backend.models.aplicacion import Aplicacion
from backend.models.aprendiz_perfil import AprendizPerfil
from backend.models.entrevista import Entrevista
from backend.models.usuario import Usuario
from backend.models.enums import RolEnum, EstadoCohorte
from backend.schemas import EntrevistaCreate, EntrevistaResponse
from backend.services.query_service import paginate_query
from backend.services.state_engine import aplicar_estado
from backend.utils.pagination import PaginationParams

router = APIRouter(prefix="/entrevistas", tags=["Entrevistas"])


def _verificar_cohorte_activa_para_entrevista(db: Session, usuario: Usuario, app: Aplicacion) -> None:
    if usuario.rol != RolEnum.APRENDIZ:
        return
    perfil = db.query(AprendizPerfil).filter(AprendizPerfil.usuario_id == usuario.id).first()
    if not perfil or not perfil.cohorte or perfil.cohorte.estado != EstadoCohorte.ACTIVA:
        raise HTTPException(
            status_code=403,
            detail="No puedes registrar entrevistas. La cohorte no está activa.",
        )


@router.get("/por-aplicacion/{app_id}", response_model=list[EntrevistaResponse])
def entrevistas_por_aplicacion(
    app_id: uuid.UUID,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any),
):
    app = db.query(Aplicacion).filter(Aplicacion.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Aplicación no encontrada.")
    if current_user.rol == RolEnum.APRENDIZ and app.usuario_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sin permisos.")
    query = db.query(Entrevista).filter(Entrevista.aplicacion_id == app_id).order_by(Entrevista.fecha)
    items, _ = paginate_query(query, pagination)
    return items


@router.get("/{entrevista_id}", response_model=EntrevistaResponse)
def obtener_entrevista(
    entrevista_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_any),
):
    e = db.query(Entrevista).filter(Entrevista.id == entrevista_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="Entrevista no encontrada.")
    return e


@router.post("/", response_model=EntrevistaResponse, status_code=201)
def crear_entrevista(
    payload: EntrevistaCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_aprendiz),
):
    """
    Crea una entrevista y recalcula el estado de la aplicación padre.
    Validaciones condicionales (grupal, fallas, subfallas) en el schema.
    """
    app = db.query(Aplicacion).filter(
        Aplicacion.id == payload.aplicacion_id,
        Aplicacion.usuario_id == current_user.id,
    ).first()
    if not app:
        raise HTTPException(status_code=404, detail="Aplicación no encontrada.")

    _verificar_cohorte_activa_para_entrevista(db, current_user, app)

    entrevista = Entrevista(
        aplicacion_id=payload.aplicacion_id,
        tipo=payload.tipo,
        modalidad=payload.modalidad,
        fecha=payload.fecha,
        grupal=payload.grupal,
        percepcion_grupal=payload.percepcion_grupal,
        fallas=[f.value for f in payload.fallas],
        subfallas=payload.subfallas,
        temas_tecnicos=[t.value for t in payload.temas_tecnicos],
        autoevaluacion=payload.autoevaluacion,
        reflexion_bien=payload.reflexion_bien,
        reflexion_mejorar=payload.reflexion_mejorar,
        respuesta_empresa=payload.respuesta_empresa,
    )
    db.add(entrevista)
    db.flush()

    # Recalcular estado de la aplicación con todas las entrevistas (incluyendo la nueva)
    todas = db.query(Entrevista).filter(Entrevista.aplicacion_id == app.id).all()
    aplicar_estado(app, todas)

    registrar(db, "CREATE_ENTREVISTA", usuario_id=current_user.id,
              detalle={
                  "aplicacion_id": str(app.id),
                  "tipo": payload.tipo.value,
                  "nuevo_estado_app": app.estado.value,
              },
              ip=request.headers.get("x-forwarded-for", request.client.host))
    db.commit()
    db.refresh(entrevista)
    return entrevista
