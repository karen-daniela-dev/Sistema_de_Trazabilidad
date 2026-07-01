"""
schemas/coordinator_dashboard.py

DTOs exclusivos del Dashboard del Coordinador.

Principios:

- No exponen entidades ORM.
- Reutilizan componentes existentes cuando es posible.
- Mantienen independencia del frontend.
- Compatibles con Pydantic v2.
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel

from backend.schemas.tutor_dashboard import (
    GoalProgressResponse,
    TutorApprenticePage,
)
from backend.utils.pagination import Page


# =============================================================================
# SELECTOR DE COHORTES
# =============================================================================


class CohortOptionResponse(BaseModel):
    """
    Cohorte disponible para el selector.

    Se envían ordenadas de la más reciente
    a la más antigua.
    """

    model_config = {"from_attributes": True}

    id: uuid.UUID

    nombre: str


# =============================================================================
# TARJETAS SUPERIORES
# =============================================================================


class CoordinatorSummaryCardsResponse(BaseModel):
    """
    Tarjetas principales del dashboard.
    """

    model_config = {"from_attributes": True}

    total_aprendices: int

    contratados: int

    no_contratados: int


class CoordinatorSummaryResponse(BaseModel):
    """
    Encabezado del dashboard.

    Contiene:

    - Barra de meta.
    - Tarjetas superiores.
    """

    model_config = {"from_attributes": True}

    goal: GoalProgressResponse

    cards: CoordinatorSummaryCardsResponse


# =============================================================================
# RANKING
# =============================================================================


class CoordinatorRankingRowResponse(BaseModel):
    """
    Información utilizada para el ranking
    de tutores.
    """

    model_config = {"from_attributes": True}

    tutor_id: uuid.UUID

    nombre: str

    score: float

    contratados: int


# =============================================================================
# TABLA DE TUTORES
# =============================================================================


class CoordinatorTutorRowResponse(BaseModel):
    """
    Representa una fila de la tabla principal
    de tutores.
    """

    model_config = {"from_attributes": True}

    tutor_id: uuid.UUID

    nombre: str

    total_aprendices: int

    contratados: int

    no_contratados: int

    porcentaje_meta: float

    score: float


CoordinatorTutorPage = Page[CoordinatorTutorRowResponse]


# =============================================================================
# DETALLE DEL TUTOR
# =============================================================================


class CoordinatorTutorDetailResponse(BaseModel):
    """
    Información mostrada al seleccionar
    un tutor.

    Reutiliza la tabla del Dashboard
    del Tutor para listar aprendices.
    """

    model_config = {"from_attributes": True}

    tutor_id: uuid.UUID

    nombre: str

    aprendices: TutorApprenticePage