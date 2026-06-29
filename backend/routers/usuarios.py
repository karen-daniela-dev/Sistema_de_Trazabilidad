"""
Router de usuarios — gestión de tutores, perfiles de aprendiz.
"""
import uuid
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies.auth import (
    require_coordinador, require_any, require_aprendiz
)
from backend.middleware.audit_middleware import registrar
from backend.models.enums import EstadoUsuario, RolEnum
from backend.models.usuario import Usuario
from backend.models.aprendiz_perfil import AprendizPerfil
from backend.models.cohorte import Cohorte
from backend.schemas import (
    CrearTutorRequest, UsuarioResponse, UsuarioListResponse,
    PerfilAprendizCreate, PerfilAprendizUpdate, PerfilAprendizResponse,
)
from backend.services.email_service import send_activation_email
from backend.services.query_service import build_page, paginate_query
from backend.utils.pagination import PaginationParams, Page
from backend.utils.security import create_access_token

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


@router.get("/", response_model=Page[UsuarioListResponse])
def listar_usuarios(
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_coordinador),
):
    query = (
        db.query(
            Usuario.id,
            Usuario.email,
            Usuario.rol,
            Usuario.estado,
            Usuario.activo,
            Usuario.created_at,
        )
        .order_by(Usuario.created_at.desc())
    )
    rows, total = paginate_query(query, pagination)
    items = [
        UsuarioListResponse(
            id=row.id,
            email=row.email,
            rol=row.rol,
            estado=row.estado,
            activo=row.activo,
            created_at=row.created_at,
        )
        for row in rows
    ]
    return build_page(items, total, pagination)


@router.get("/tutores", response_model=list[UsuarioListResponse])
def listar_tutores(
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_any),
):
    rows = (
        db.query(
            Usuario.id,
            Usuario.email,
            Usuario.rol,
            Usuario.estado,
            Usuario.activo,
            Usuario.created_at,
        )
        .filter(Usuario.rol == RolEnum.TUTOR, Usuario.activo == True)
        .all()
    )
    return [
        UsuarioListResponse(
            id=row.id,
            email=row.email,
            rol=row.rol,
            estado=row.estado,
            activo=row.activo,
            created_at=row.created_at,
        )
        for row in rows
    ]


@router.post("/tutor", response_model=UsuarioResponse, status_code=201)
def crear_tutor(
    payload: CrearTutorRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_coordinador),
):
    """
    Crea un tutor en estado PENDIENTE y envía email de activación.
    """
    if db.query(Usuario).filter(Usuario.email == payload.email).first():
        raise HTTPException(status_code=400, detail="El email ya está registrado.")

    tutor = Usuario(
        email=payload.email,
        password_hash="__pending__",  # se establece en activación
        rol=RolEnum.TUTOR,
        estado=EstadoUsuario.PENDIENTE,
        activo=True,
    )
    db.add(tutor)
    db.flush()

    # Token de activación de 24h con purpose específico
    activation_token = create_access_token(
        {"sub": str(tutor.id), "purpose": "activation"},
        expires_delta=timedelta(hours=24),
    )
    send_activation_email(payload.email, activation_token)

    registrar(db, "REGISTER_TUTOR", usuario_id=current_user.id,
              detalle={"tutor_email": payload.email},
              ip=request.headers.get("x-forwarded-for", request.client.host))
    db.commit()
    db.refresh(tutor)
    return tutor


# ── Perfil Aprendiz ───────────────────────────────────────────────────────────

@router.post("/perfil", response_model=PerfilAprendizResponse, status_code=201)
def crear_perfil(
    payload: PerfilAprendizCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_aprendiz),
):
    # Validar que cohorte existe y está activa
    cohorte = db.query(Cohorte).filter(Cohorte.id == payload.cohorte_id).first()
    if not cohorte:
        raise HTTPException(status_code=404, detail="Cohorte no encontrada.")

    # Validar que tutor existe
    tutor = db.query(Usuario).filter(
        Usuario.id == payload.tutor_id, Usuario.rol == RolEnum.TUTOR
    ).first()
    if not tutor:
        raise HTTPException(status_code=404, detail="Tutor no encontrado.")

    # Un aprendiz solo puede tener un perfil
    if db.query(AprendizPerfil).filter(AprendizPerfil.usuario_id == current_user.id).first():
        raise HTTPException(status_code=400, detail="El aprendiz ya tiene un perfil registrado.")

    perfil = AprendizPerfil(
        usuario_id=current_user.id,
        cohorte_id=payload.cohorte_id,
        tutor_id=payload.tutor_id,
        telefono=payload.telefono,
        telefono_emergencia=payload.telefono_emergencia,
        ciudad=payload.ciudad,
    )
    db.add(perfil)
    registrar(db, "UPDATE_PERFIL", usuario_id=current_user.id)
    db.commit()
    db.refresh(perfil)
    return perfil


@router.get("/perfil/me", response_model=PerfilAprendizResponse)
def mi_perfil(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_aprendiz),
):
    perfil = db.query(AprendizPerfil).filter(
        AprendizPerfil.usuario_id == current_user.id
    ).first()
    if not perfil:
        raise HTTPException(status_code=404, detail="Perfil no encontrado. Complete su perfil.")
    return perfil


@router.patch("/perfil/me", response_model=PerfilAprendizResponse)
def actualizar_mi_perfil(
    payload: PerfilAprendizUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_aprendiz),
):
    """Aprendiz puede editar solo teléfono y ciudad — NO cohorte ni tutor."""
    perfil = db.query(AprendizPerfil).filter(
        AprendizPerfil.usuario_id == current_user.id
    ).first()
    if not perfil:
        raise HTTPException(status_code=404, detail="Perfil no encontrado.")

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(perfil, field, value)

    registrar(db, "UPDATE_PERFIL", usuario_id=current_user.id,
              ip=request.headers.get("x-forwarded-for", request.client.host))
    db.commit()
    db.refresh(perfil)
    return perfil


@router.get("/{usuario_id}/perfil", response_model=PerfilAprendizResponse)
def perfil_por_id(
    usuario_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_any),
):
    perfil = db.query(AprendizPerfil).filter(AprendizPerfil.usuario_id == usuario_id).first()
    if not perfil:
        raise HTTPException(status_code=404, detail="Perfil no encontrado.")
    return perfil
