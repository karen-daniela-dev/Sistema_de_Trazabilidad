"""
services/coordinator_dashboard_queries.py

Consultas SQL especializadas para el Dashboard del Coordinador.

Responsabilidades:

- Recuperar información desde PostgreSQL.
- No calcular KPIs.
- No construir DTOs.
- No contener reglas de negocio.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import case, func
from sqlalchemy.orm import Session, selectinload

from backend.models.aplicacion import Aplicacion
from backend.models.aprendiz_perfil import AprendizPerfil
from backend.models.cohorte import Cohorte
from backend.models.enums import EstadoApp, RolEnum
from backend.models.usuario import Usuario
from backend.utils.pagination import PaginationParams


class CoordinatorDashboardQueries:

    # -------------------------------------------------------------------------
    # Cohortes
    # -------------------------------------------------------------------------

    @staticmethod
    def get_cohortes(
        db: Session,
    ) -> list[Cohorte]:
        """
        Retorna las cohortes ordenadas desde
        la más reciente hasta la más antigua.
        """

        return (
            db.query(Cohorte)
            .order_by(
                Cohorte.fecha_inicio.desc()
            )
            .all()
        )

    @staticmethod
    def get_cohorte(
        db: Session,
        cohorte_id: UUID,
    ) -> Cohorte | None:
        """
        Recupera una cohorte específica.
        """

        return (
            db.query(Cohorte)
            .filter(
                Cohorte.id == cohorte_id,
            )
            .first()
        )

    # -------------------------------------------------------------------------
    # Resumen de cohorte
    # -------------------------------------------------------------------------

    @staticmethod
    def get_cohorte_summary(
        db: Session,
        cohorte_id: UUID,
    ):
        """
        Devuelve los datos necesarios para
        construir las tarjetas superiores.
        """

        return (
            db.query(
                Cohorte.id,
                Cohorte.nombre,
                Cohorte.meta_contratacion,

                func.count(
                    func.distinct(
                        AprendizPerfil.usuario_id
                    )
                ).label("total_aprendices"),

                func.count(
                    func.distinct(
                        case(
                            (
                                Aplicacion.estado == EstadoApp.CONTRATADO,
                                Aplicacion.usuario_id,
                            )
                        )
                    )
                ).label("contratados"),
            )

            .outerjoin(
                AprendizPerfil,
                AprendizPerfil.cohorte_id == Cohorte.id,
            )

            .outerjoin(
                Aplicacion,
                Aplicacion.usuario_id == AprendizPerfil.usuario_id,
            )

            .filter(
                Cohorte.id == cohorte_id,
            )

            .group_by(
                Cohorte.id,
                Cohorte.nombre,
                Cohorte.meta_contratacion,
            )

            .first()
        )

    # -------------------------------------------------------------------------
    # Ranking de tutores
    # -------------------------------------------------------------------------

    @staticmethod
    def get_tutor_ranking(
        db: Session,
        cohorte_id: UUID,
    ):
        """
        Ranking base de tutores.

        El Service calculará el score final.
        """

        return (

            db.query(

                Usuario.id.label("tutor_id"),

                Usuario.email,

                func.count(
                    func.distinct(
                        AprendizPerfil.usuario_id
                    )
                ).label(
                    "total_aprendices"
                ),

                func.count(
                    Aplicacion.id
                ).label(
                    "total_aplicaciones"
                ),

                func.count(
                    func.distinct(
                        case(
                            (
                                Aplicacion.estado == EstadoApp.CONTRATADO,
                                Aplicacion.usuario_id,
                            )
                        )
                    )
                ).label(
                    "contratados"
                ),
            )

            .join(
                AprendizPerfil,
                AprendizPerfil.tutor_id == Usuario.id,
            )

            .outerjoin(
                Aplicacion,
                Aplicacion.usuario_id == AprendizPerfil.usuario_id,
            )

            .filter(
                Usuario.rol == RolEnum.TUTOR,
                AprendizPerfil.cohorte_id == cohorte_id,
            )

            .group_by(
                Usuario.id,
                Usuario.email,
            )

            .all()
        )

    # -------------------------------------------------------------------------
    # Tabla paginada de tutores
    # -------------------------------------------------------------------------

    @staticmethod
    def get_tutores_page(
        db: Session,
        cohorte_id: UUID,
        pagination: PaginationParams,
    ):
        """
        Recupera una página de tutores.
        """

        return (

            db.query(

                Usuario,

                func.count(
                    func.distinct(
                        AprendizPerfil.usuario_id
                    )
                ).label(
                    "total_aprendices"
                ),

                func.count(
                    Aplicacion.id
                ).label(
                    "total_aplicaciones"
                ),

                func.count(
                    func.distinct(
                        case(
                            (
                                Aplicacion.estado == EstadoApp.CONTRATADO,
                                Aplicacion.usuario_id,
                            )
                        )
                    )
                ).label(
                    "contratados"
                ),
            )

            .join(
                AprendizPerfil,
                AprendizPerfil.tutor_id == Usuario.id,
            )

            .outerjoin(
                Aplicacion,
                Aplicacion.usuario_id == AprendizPerfil.usuario_id,
            )

            .filter(
                Usuario.rol == RolEnum.TUTOR,
                AprendizPerfil.cohorte_id == cohorte_id,
            )

            .group_by(
                Usuario.id,
            )

            .order_by(
                Usuario.email,
            )

            .offset(
                pagination.offset,
            )

            .limit(
                pagination.size,
            )

            .all()
        )

    @staticmethod
    def count_tutores(
        db: Session,
        cohorte_id: UUID,
    ) -> int:
        """
        Total de tutores de una cohorte.
        """

        return (

            db.query(
                Usuario.id,
            )

            .join(
                AprendizPerfil,
                AprendizPerfil.tutor_id == Usuario.id,
            )

            .filter(
                Usuario.rol == RolEnum.TUTOR,
                AprendizPerfil.cohorte_id == cohorte_id,
            )

            .distinct()

            .count()
        )

    # -------------------------------------------------------------------------
    # Aprendices del tutor
    # -------------------------------------------------------------------------

    @staticmethod
    def get_aprendices_tutor(
        db: Session,
        tutor_id: UUID,
        cohorte_id: UUID,
    ) -> list[AprendizPerfil]:
        """
        Recupera los aprendices pertenecientes
        a un tutor dentro de una cohorte.
        """

        return (

            db.query(AprendizPerfil)

            .options(
                selectinload(
                    AprendizPerfil.usuario,
                )
            )

            .filter(
                AprendizPerfil.tutor_id == tutor_id,
                AprendizPerfil.cohorte_id == cohorte_id,
            )

            .all()
        )