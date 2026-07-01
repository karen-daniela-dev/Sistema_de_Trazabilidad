#backend/routers/coordinator_dashboard.py

from uuid import UUID

from backend.schemas.tutor_dashboard import TutorApprenticeDetailResponse, TutorFailureSummaryResponse
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies.auth import require_coordinador
from backend.models.usuario import Usuario

from backend.schemas.coordinator_dashboard import (
    CohortOptionResponse,
    CoordinatorSummaryResponse,
    CoordinatorRankingRowResponse,
    CoordinatorTutorPage,
    CoordinatorTutorDetailResponse,
)

from backend.services.coordinator_dashboard_service import (
    CoordinatorDashboardService,
)

from backend.utils.pagination import PaginationParams


router = APIRouter(
    prefix="/dashboard/coordinator",
    tags=["Dashboard Coordinador"],
)


# -----------------------------------------------------------------------------
# Cohortes
# -----------------------------------------------------------------------------

@router.get(
    "/cohortes",
    response_model=list[CohortOptionResponse],
)
def get_cohortes(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_coordinador),
):

    return CoordinatorDashboardService.get_cohortes(
        db,
    )


# -----------------------------------------------------------------------------
# Resumen
# -----------------------------------------------------------------------------

@router.get(
    "/summary",
    response_model=CoordinatorSummaryResponse,
)
def get_summary(

    cohorte_id: UUID,

    db: Session = Depends(get_db),

    current_user: Usuario = Depends(require_coordinador),
):

    return CoordinatorDashboardService.get_summary(

        db,

        cohorte_id,
    )


# -----------------------------------------------------------------------------
# Ranking
# -----------------------------------------------------------------------------

@router.get(
    "/ranking",
    response_model=list[CoordinatorRankingRowResponse],
)
def get_ranking(

    cohorte_id: UUID,

    db: Session = Depends(get_db),

    current_user: Usuario = Depends(require_coordinador),
):

    return CoordinatorDashboardService.get_ranking(

        db,

        cohorte_id,
    )


# -----------------------------------------------------------------------------
# Tabla de tutores
# -----------------------------------------------------------------------------

@router.get(
    "/tutors",
    response_model=CoordinatorTutorPage,
)
def get_tutores(

    cohorte_id: UUID,

    pagination: PaginationParams = Depends(),

    db: Session = Depends(get_db),

    current_user: Usuario = Depends(require_coordinador),
):

    return CoordinatorDashboardService.get_tutores_page(

        db=db,

        cohorte_id=cohorte_id,

        pagination=pagination,
    )


# -----------------------------------------------------------------------------
# Aprendices del tutor
# -----------------------------------------------------------------------------

@router.get(
    "/tutors/{tutor_id}/apprentices",
    response_model=CoordinatorTutorDetailResponse,
)
def get_tutor_detail(

    tutor_id: UUID,

    cohorte_id: UUID,

    pagination: PaginationParams = Depends(),

    db: Session = Depends(get_db),

    current_user: Usuario = Depends(require_coordinador),
):

    return CoordinatorDashboardService.get_tutor_detail(

        db=db,

        cohorte_id=cohorte_id,

        tutor_id=tutor_id,

        pagination=pagination,
    )

@router.get(
    "/apprentices/{aprendiz_id}",
    response_model=TutorApprenticeDetailResponse,
)
def get_apprentice_detail(

    aprendiz_id: UUID,

    cohorte_id: UUID,

    db: Session = Depends(get_db),

    current_user: Usuario = Depends(require_coordinador),

):

    return CoordinatorDashboardService.get_apprentice_detail(

        db=db,

        cohorte_id=cohorte_id,

        aprendiz_id=aprendiz_id,
    )
@router.get(
    "/apprentices/{aprendiz_id}/failures",
    response_model=TutorFailureSummaryResponse,
)
def get_apprentice_failures(

    aprendiz_id: UUID,

    cohorte_id: UUID,

    db: Session = Depends(get_db),

    current_user: Usuario = Depends(require_coordinador),

):

    return CoordinatorDashboardService.get_apprentice_failures(

        db=db,

        cohorte_id=cohorte_id,

        aprendiz_id=aprendiz_id,
    )
