"""Helpers reutilizables para consultas y paginación."""
from __future__ import annotations

from typing import Sequence, TypeVar
from uuid import UUID

from sqlalchemy.orm import Session

from backend.models.aprendiz_perfil import AprendizPerfil
from backend.models.aplicacion import Aplicacion
from backend.models.usuario import Usuario
from backend.models.enums import RolEnum
from backend.utils.pagination import PaginationParams, Page
#query_service.py
T = TypeVar("T")


def get_tutor_aprendiz_ids(db: Session, tutor_id: UUID) -> list[UUID]:
    """Devuelve los ids de los aprendices de un tutor en una sola consulta."""
    rows = (
        db.query(AprendizPerfil.usuario_id)
        .filter(AprendizPerfil.tutor_id == tutor_id)
        .all()
    )
    return [row[0] for row in rows]


def paginate_query(query, pagination: PaginationParams) -> tuple[list, int]:
    total = query.count()
    items = query.offset(pagination.offset).limit(pagination.size).all()
    return items, total


def build_page(items: Sequence[T], total: int, pagination: PaginationParams) -> Page[T]:
    return Page.build(items, total, pagination)


def get_visible_applications_query(db: Session, current_user: Usuario):
    query = db.query(Aplicacion)

    if current_user.rol == RolEnum.APRENDIZ:
        query = query.filter(Aplicacion.usuario_id == current_user.id)
    elif current_user.rol == RolEnum.TUTOR:
        aprendiz_ids = get_tutor_aprendiz_ids(db, current_user.id)
        query = query.filter(Aplicacion.usuario_id.in_(aprendiz_ids))

    return query
