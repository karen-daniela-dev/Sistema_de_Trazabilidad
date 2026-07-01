"""
services/coordinator_dashboard_service.py

Servicio principal del Dashboard del Coordinador.

Responsabilidades:

- Orquestar consultas.
- Construir DTOs.
- Reutilizar la lógica existente del Dashboard Tutor.
- No ejecutar consultas SQL directamente.
"""

from __future__ import annotations

from uuid import UUID
from backend.models import usuario
from backend.services.tutor_dashboard_queries import TutorDashboardQueries
from backend.services.tutor_score import build_tutor_score

from backend.services.user_helpers import display_name
from sqlalchemy.orm import Session

from backend.schemas.coordinator_dashboard import (
    CohortOptionResponse,
    CoordinatorSummaryCardsResponse,
    CoordinatorSummaryResponse,
    CoordinatorRankingRowResponse,
    CoordinatorTutorRowResponse,
    CoordinatorTutorPage,
    CoordinatorTutorDetailResponse,
)

from backend.schemas.tutor_dashboard import (
    GoalProgressResponse,
    TutorApprenticeDetailResponse,
    TutorFailureSummaryResponse,
)

from backend.services.coordinator_dashboard_queries import (
    CoordinatorDashboardQueries,
)

from backend.services.tutor_dashboard_service import (
    TutorDashboardService,
)

from backend.utils.pagination import (
    PaginationParams,
)


class CoordinatorDashboardService:

    # ------------------------------------------------------------------
    # Cohortes
    # ------------------------------------------------------------------

    @staticmethod
    def get_cohortes(
        db: Session,
    ) -> list[CohortOptionResponse]:

        cohortes = CoordinatorDashboardQueries.get_cohortes(
            db,
        )

        return [

            CohortOptionResponse(
                id=cohorte.id,
                nombre=cohorte.nombre,
            )

            for cohorte in cohortes
        ]

    # ------------------------------------------------------------------
    # Resumen
    # ------------------------------------------------------------------

    @staticmethod
    def get_summary(
        db: Session,
        cohorte_id: UUID,
    ) -> CoordinatorSummaryResponse:

        row = CoordinatorDashboardQueries.get_cohorte_summary(
            db,
            cohorte_id,
        )

        if row is None:

            raise ValueError(
                "La cohorte no existe."
            )

        total = row.total_aprendices or 0

        contratados = row.contratados or 0

        no_contratados = max(
            0,
            total - contratados,
        )

        meta = row.meta_contratacion or 0

        porcentaje_actual = (
            (contratados / total) * 100
            if total
            else 0
        )

        porcentaje_cumplimiento = (
            (contratados / meta) * 100
            if meta
            else 0
        )

        faltantes = max(
            0,
            meta - contratados,
        )

        sobrecumplimiento = max(
            0,
            contratados - meta,
        )

        return CoordinatorSummaryResponse(

            goal=GoalProgressResponse(

                porcentaje_meta=100,

                porcentaje_actual=round(
                    porcentaje_actual,
                    2,
                ),

                porcentaje_cumplimiento=round(
                    porcentaje_cumplimiento,
                    2,
                ),

                total_aprendices=total,

                meta_contratados=meta,

                contratados=contratados,

                faltantes=faltantes,

                sobrecumplimiento=sobrecumplimiento,

                meta_alcanzada=contratados >= meta,

                sobrecumplida=sobrecumplimiento > 0,
            ),

            cards=CoordinatorSummaryCardsResponse(

                total_aprendices=total,

                contratados=contratados,

                no_contratados=no_contratados,
            ),
        )

    # ------------------------------------------------------------------
    # Ranking
    # ------------------------------------------------------------------

    @staticmethod
    def get_ranking(
        db: Session,
        cohorte_id: UUID,
    ) -> list[CoordinatorRankingRowResponse]:

        rows = CoordinatorDashboardQueries.get_tutor_ranking(
            db,
            cohorte_id,
        )

        ranking: list[CoordinatorRankingRowResponse] = []

        for row in rows:

            metrics = build_tutor_score(
                total_aprendices=row.total_aprendices or 0,
                total_aplicaciones=row.total_aplicaciones or 0,
                contratados=row.contratados or 0,
            )

            ranking.append(

                CoordinatorRankingRowResponse(

                    tutor_id=row.tutor_id,

                    nombre=display_name(row),

                    score=metrics["score"],

                    contratados=row.contratados or 0,
                )
            )

        ranking.sort(
            key=lambda item: item.score,
            reverse=True,
        )

        return ranking

    # ------------------------------------------------------------------
    # Tabla de tutores
    # ------------------------------------------------------------------
    @staticmethod
    def get_tutores_page(
        db: Session,
        cohorte_id: UUID,
        pagination: PaginationParams,
    ) -> CoordinatorTutorPage:

        rows = CoordinatorDashboardQueries.get_tutores_page(
            db,
            cohorte_id,
            pagination,
        )

        total = CoordinatorDashboardQueries.count_tutores(
            db,
            cohorte_id,
        )

        items: list[CoordinatorTutorRowResponse] = []

        for usuario, total_aprendices, total_aplicaciones, contratados in rows:

            total_aprendices = total_aprendices or 0
            total_aplicaciones = total_aplicaciones or 0
            contratados = contratados or 0

            metrics = build_tutor_score(
                total_aprendices=total_aprendices,
                total_aplicaciones=total_aplicaciones,
                contratados=contratados,
            )

            items.append(

                CoordinatorTutorRowResponse(

                    tutor_id=usuario.id,

                    nombre=display_name(usuario),

                    total_aprendices=total_aprendices,

                    contratados=contratados,

                    no_contratados=max(
                        0,
                        total_aprendices - contratados,
                    ),

                    porcentaje_meta=round(
                        (contratados / total_aprendices) * 100,
                        2,
                    )
                    if total_aprendices
                    else 0,

                    score=metrics["score"],
                )
            )

        return CoordinatorTutorPage.build(

            items=items,

            total=total,

            params=pagination,
        )
   

    # ------------------------------------------------------------------
    # Detalle del tutor
    # ------------------------------------------------------------------

    @staticmethod
    def get_tutor_detail(
        db: Session,
        cohorte_id: UUID,
        tutor_id: UUID,
        pagination: PaginationParams,
    ) -> CoordinatorTutorDetailResponse:

        page = TutorDashboardService.get_apprentices_page(

            db=db,

            tutor_id=tutor_id,
            

            pagination=pagination,
        )

        tutor = CoordinatorDashboardQueries.get_tutor_ranking(
            db,
            cohorte_id,
        )

        selected = next(
            (
                item
                for item in tutor
                if item.tutor_id == tutor_id
            ),
            None,
        )

        if selected is None:

            raise ValueError(
                "Tutor no encontrado."
            )

        return CoordinatorTutorDetailResponse(

            tutor_id=selected.tutor_id,

            nombre=display_name(selected),

            aprendices=page,
        )
    @staticmethod
    def get_apprentice_detail(
        db: Session,
        cohorte_id: UUID,
        aprendiz_id: UUID,
    ) -> TutorApprenticeDetailResponse:

        perfil = TutorDashboardQueries.get_aprendiz(
            db,
            aprendiz_id,
            cohorte_id=cohorte_id,
        )

        if perfil is None:
            raise ValueError(
                "El aprendiz no pertenece a la cohorte."
            )

        return TutorDashboardService._build_apprentice_detail(
            db,
            perfil,
        )
    @staticmethod
    def get_apprentice_failures(
        db: Session,
        cohorte_id: UUID,
        aprendiz_id: UUID,
    ) -> TutorFailureSummaryResponse:
        """
        Obtiene el resumen de fallas de un aprendiz
        desde el Dashboard del Coordinador.
        """

        perfil = TutorDashboardQueries.get_aprendiz(
            db,
            aprendiz_id,
            cohorte_id=cohorte_id,
        )

        if perfil is None:

            raise ValueError(
                "El aprendiz no pertenece a la cohorte."
            )

        return TutorDashboardService._build_failure_summary(
            db,
            aprendiz_id,
        )    