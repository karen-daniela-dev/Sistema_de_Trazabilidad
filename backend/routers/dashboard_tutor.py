from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies.auth import require_tutor
from backend.models.usuario import Usuario

from backend.schemas.tutor_dashboard import (
    TutorSummaryResponse,
    TutorApprenticePage,
    TutorApprenticeDetailResponse,
    TutorApplicationPage,
    TutorReflectionPage,
    TutorFailureSummaryResponse,
    TutorApprenticeFilters,
)

from backend.services.tutor_dashboard_service import (
    TutorDashboardService,
)

from backend.utils.pagination import PaginationParams

router = APIRouter(
    prefix="/dashboard/tutor",
    tags=["Dashboard Tutor"],
)

@router.get(
    "/summary",
    response_model=TutorSummaryResponse,
)
def get_summary(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_tutor),
):

    return TutorDashboardService.get_summary(
        db,
        current_user.id,
    )
    
@router.get(
    "/apprentices",
    response_model=TutorApprenticePage,
)
def get_apprentices(

    filters: TutorApprenticeFilters = Depends(),

    pagination: PaginationParams = Depends(),

    db: Session = Depends(get_db),

    current_user: Usuario = Depends(require_tutor),
):

    return TutorDashboardService.get_apprentices_page(

        db=db,

        tutor_id=current_user.id,

        filters=filters,

        pagination=pagination,
    )
@router.get(
    "/apprentices/{aprendiz_id}",
    response_model=TutorApprenticeDetailResponse,
)
def get_apprentice_detail(

    aprendiz_id: UUID,

    db: Session = Depends(get_db),

    current_user: Usuario = Depends(require_tutor),
):

    return TutorDashboardService.get_apprentice_detail(

        db,

        current_user.id,

        aprendiz_id,
    )
    
@router.get(
    "/apprentices/{aprendiz_id}/applications",
    response_model=TutorApplicationPage,
)
def get_applications(

    aprendiz_id: UUID,

    pagination: PaginationParams = Depends(),

    db: Session = Depends(get_db),

    current_user: Usuario = Depends(require_tutor),
):

    return TutorDashboardService.get_applications(

        db=db,

        tutor_id=current_user.id,

        aprendiz_id=aprendiz_id,

        pagination=pagination,
    )  

@router.get(
    "/apprentices/{aprendiz_id}/reflections",
    response_model=TutorReflectionPage,
)
def get_reflections(

    aprendiz_id: UUID,

    pagination: PaginationParams = Depends(),

    db: Session = Depends(get_db),

    current_user: Usuario = Depends(require_tutor),
):

    return TutorDashboardService.get_reflections(

        db=db,

        tutor_id=current_user.id,

        aprendiz_id=aprendiz_id,

        pagination=pagination,
    ) 
@router.get(
    "/apprentices/{aprendiz_id}/failures",
    response_model=TutorFailureSummaryResponse,
)
def get_failure_summary(

    aprendiz_id: UUID,

    db: Session = Depends(get_db),

    current_user: Usuario = Depends(require_tutor),
):

    return TutorDashboardService.get_failure_summary(

        db,

        current_user.id,

        aprendiz_id,
    )