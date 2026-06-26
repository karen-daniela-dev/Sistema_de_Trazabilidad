"""
Router de cohortes — solo COORDINADOR puede crear/editar.
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies.auth import require_coordinador, require_any
from backend.middleware.audit_middleware import registrar
from backend.models.cohorte import Cohorte
from backend.models.usuario import Usuario
from backend.schemas import CohorteCreate, CohorteUpdate, CohorteResponse, CohorteListResponse
from backend.services.cohort_engine import fecha_fin_desde_inicio, sincronizar_estados_cohortes
from backend.services.query_service import paginate_query
from backend.utils.pagination import PaginationParams, Page

router = APIRouter(prefix="/cohortes", tags=["Cohortes"])


@router.get("/", response_model=Page[CohorteListResponse])
def listar_cohortes(
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_any),
):
    query = (
        db.query(
            Cohorte.id,
            Cohorte.nombre,
            Cohorte.fecha_inicio,
            Cohorte.fecha_fin,
            Cohorte.estado,
            Cohorte.meta_contratacion,
            Cohorte.permitir_extension,
            Cohorte.created_at,
        )
        .order_by(Cohorte.fecha_inicio.desc())
    )
    rows, total = paginate_query(query, pagination)
    items = [
        CohorteListResponse(
            id=row.id,
            nombre=row.nombre,
            fecha_inicio=row.fecha_inicio,
            fecha_fin=row.fecha_fin,
            estado=row.estado,
            meta_contratacion=row.meta_contratacion,
            permitir_extension=row.permitir_extension,
            created_at=row.created_at,
        )
        for row in rows
    ]
    return Page.build(items, total, pagination)


@router.get("/{cohorte_id}", response_model=CohorteResponse)
def obtener_cohorte(
    cohorte_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_any),
):
    c = db.query(Cohorte).filter(Cohorte.id == cohorte_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Cohorte no encontrada.")
    return c


@router.post("/", response_model=CohorteResponse, status_code=201)
def crear_cohorte(
    payload: CohorteCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_coordinador),
):
    cohorte = Cohorte(
        nombre=payload.nombre,
        fecha_inicio=payload.fecha_inicio,
        fecha_fin=fecha_fin_desde_inicio(payload.fecha_inicio),
        meta_contratacion=payload.meta_contratacion,
        permitir_extension=payload.permitir_extension,
    )
    db.add(cohorte)
    db.flush()
    registrar(db, "CREATE_COHORTE", usuario_id=current_user.id,
              detalle={"nombre": cohorte.nombre},
              ip=request.headers.get("x-forwarded-for", request.client.host))
    db.commit()
    db.refresh(cohorte)
    return cohorte


@router.patch("/{cohorte_id}", response_model=CohorteResponse)
def actualizar_cohorte(
    cohorte_id: uuid.UUID,
    payload: CohorteUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_coordinador),
):
    c = db.query(Cohorte).filter(Cohorte.id == cohorte_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Cohorte no encontrada.")

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(c, field, value)

    registrar(db, "UPDATE_COHORTE", usuario_id=current_user.id,
              detalle={"cohorte_id": str(cohorte_id), **payload.model_dump(exclude_none=True)},
              ip=request.headers.get("x-forwarded-for", request.client.host))
    db.commit()
    db.refresh(c)
    return c


@router.post("/sincronizar-estados", status_code=200)
def sincronizar(
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_coordinador),
):
    """Sincroniza manualmente los estados de todas las cohortes."""
    n = sincronizar_estados_cohortes(db)
    return {"cohortes_actualizadas": n}
