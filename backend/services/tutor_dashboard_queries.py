"""
services/tutor_dashboard_queries.py

Consultas SQL especializadas para el Dashboard del Tutor.

IMPORTANTE

Este archivo NO contiene reglas de negocio.

Su única responsabilidad es recuperar información desde PostgreSQL
de la forma más eficiente posible.

Toda la lógica de:

- semáforos
- porcentajes
- metas
- progreso
- actividad
- construcción de DTOs

pertenece exclusivamente a:

    tutor_dashboard_service.py
"""

from __future__ import annotations

from uuid import UUID
from backend.utils.pagination import PaginationParams

from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload

from backend.models.usuario import Usuario
from backend.models.aprendiz_perfil import AprendizPerfil
from backend.models.aplicacion import Aplicacion
from backend.models.entrevista import Entrevista
from backend.models.cohorte import Cohorte
from backend.models.enums import EstadoCohorte, RolEnum


class TutorDashboardQueries:
    """
    Repositorio de consultas SQL para el Dashboard Tutor.

    Todas las funciones son estáticas porque
    no mantienen estado.

    Deben devolver únicamente entidades ORM
    o estructuras simples.

    Nunca DTOs.
    """

    # ---------------------------------------------------------------------
    # Tutor
    # ---------------------------------------------------------------------

    @staticmethod
    def get_tutor(
        db: Session,
        tutor_id: UUID,
    ) -> Usuario | None:
        """
        Obtiene el tutor.

        Se utiliza para validar existencia
        y recuperar información básica.
        """

        return (
            db.query(Usuario)
            .filter(
                Usuario.id == tutor_id,
                Usuario.rol == RolEnum.TUTOR,
                Usuario.activo.is_(True),
            )
            .first()
        )

    # ---------------------------------------------------------------------
    # Cohorte del tutor
    # ---------------------------------------------------------------------

    @staticmethod
    def get_tutor_cohorte(
        db: Session,
        tutor_id: UUID,
    ) -> Cohorte | None:
        """
        Devuelve la cohorte asociada al tutor.

        Actualmente un tutor pertenece
        a una única cohorte.
        """

        return (
            db.query(Cohorte)
            .join(
                AprendizPerfil,
                AprendizPerfil.cohorte_id == Cohorte.id,
            )
            .filter(
                AprendizPerfil.tutor_id == tutor_id,
                Cohorte.estado == EstadoCohorte.ACTIVA,
            )
            .distinct()
            .first()
        )
        
    # ---------------------------------------------------------------------
    # Aprendices del tutor
    # ---------------------------------------------------------------------


    # ---------------------------------------------------------------------
    # Aplicaciones de varios aprendices
    # ---------------------------------------------------------------------

    @staticmethod
    def get_apprentices(
        db: Session,
        tutor_id: UUID,
        cohorte_id: UUID,
    ) -> list[AprendizPerfil]:
        """
        Obtiene los aprendices asignados al tutor
        dentro de una cohorte.
        """

        return (
            db.query(AprendizPerfil)
            .options(
                selectinload(AprendizPerfil.usuario),
                selectinload(AprendizPerfil.cohorte),
            )
            .filter(
                AprendizPerfil.tutor_id == tutor_id,
                AprendizPerfil.cohorte_id == cohorte_id,
            )
            .all()
        )
            
    # ---------------------------------------------------------------------
    # Entrevistas de varias aplicaciones
    # ---------------------------------------------------------------------

    @staticmethod
    def get_entrevistas(
        db: Session,
        aplicaciones_ids: list[UUID],
    ) -> list[Entrevista]:
        """
        Recupera todas las entrevistas asociadas
        a un conjunto de aplicaciones.

        Esta consulta será reutilizada por:

        - Dashboard principal
        - Detalle del aprendiz
        - Fallas
        - Reflexiones
        """

        if not aplicaciones_ids:
            return []

        return (
            db.query(Entrevista)
            .filter(
                Entrevista.aplicacion_id.in_(aplicaciones_ids)
            )
            .all()
        )

    # ---------------------------------------------------------------------
    # Aprendiz específico
    # ---------------------------------------------------------------------

    @staticmethod
    def get_aprendiz(
        db: Session,
        aprendiz_id: UUID,
        tutor_id: UUID,
    ) -> AprendizPerfil | None:
        """
        Recupera un aprendiz verificando
        que pertenezca al tutor autenticado.

        Evita que un tutor consulte
        información de otro tutor.
        """

        return (
            db.query(AprendizPerfil)
            .options(
                selectinload(AprendizPerfil.usuario),
                selectinload(AprendizPerfil.cohorte),
            )
            .filter(
                AprendizPerfil.usuario_id == aprendiz_id,
                AprendizPerfil.tutor_id == tutor_id,
            )
            .first()
        )

    # ---------------------------------------------------------------------
    # Aplicaciones de un aprendiz
    # ---------------------------------------------------------------------

    @staticmethod
    def get_aprendiz_applications(
        db: Session,
        aprendiz_id: UUID,
    ) -> list[Aplicacion]:
        """
        Recupera todas las aplicaciones
        de un único aprendiz.

        Utilizado por el panel
        "Ver vacantes".
        """

        return (
            db.query(Aplicacion)
            .filter(
                Aplicacion.usuario_id == aprendiz_id
            )
            .order_by(
                Aplicacion.fecha_aplicacion.desc()
            )
            .all()
        )
    # ---------------------------------------------------------------------
    # Entrevistas de un aprendiz
    # ---------------------------------------------------------------------

    @staticmethod
    def get_aprendiz_entrevistas(
        db: Session,
        aprendiz_id: UUID,
    ) -> list[Entrevista]:
        """
        Recupera todas las entrevistas de un aprendiz.

        Utilizado para:

        - Reflexiones
        - Fallas
        - Estadísticas individuales
        """

        return (
            db.query(Entrevista)
            .join(
                Aplicacion,
                Aplicacion.id == Entrevista.aplicacion_id,
            )
            .filter(
                Aplicacion.usuario_id == aprendiz_id,
            )
            .order_by(
                Entrevista.fecha.desc()
            )
            .all()
        )

    # ---------------------------------------------------------------------
    # Alertas
    # ---------------------------------------------------------------------

    @staticmethod
    def get_alert_candidates(
        db: Session,
        tutor_id: UUID,
    ) -> list[AprendizPerfil]:
        """
        Recupera todos los aprendices del tutor.

        Posteriormente el Service calculará
        cuáles requieren generar alertas.

        Esta función NO aplica reglas de negocio.
        """

        return (
            db.query(AprendizPerfil)
            .options(
                selectinload(AprendizPerfil.usuario),
            )
            .filter(
                AprendizPerfil.tutor_id == tutor_id,
            )
            .all()
        )

   
    # ---------------------------------------------------------------------
    # Aplicaciones + entrevistas (Carga masiva)
    # ---------------------------------------------------------------------

    @staticmethod
    def get_applications_with_interviews(
        db: Session,
        aprendiz_ids: list[UUID],
    ) -> list[Aplicacion]:
        """
        Recupera todas las aplicaciones pertenecientes
        a un conjunto de aprendices junto con sus
        entrevistas.

        Esta consulta está optimizada para el Dashboard
        principal del Tutor y evita el problema N+1.
        """

        if not aprendiz_ids:
            return []

        return (
            db.query(Aplicacion)
            .options(
                selectinload(Aplicacion.entrevistas),
            )
            .filter(
                Aplicacion.usuario_id.in_(aprendiz_ids),
            )
            .order_by(
                Aplicacion.fecha_aplicacion.desc(),
            )
            .all()
        )

    # ---------------------------------------------------------------------
    # Verificación de pertenencia
    # ---------------------------------------------------------------------

    @staticmethod
    def aprendiz_belongs_to_tutor(
        db: Session,
        tutor_id: UUID,
        aprendiz_id: UUID,
    ) -> bool:
        """
        Verifica que un aprendiz pertenezca
        al tutor autenticado.

        Se utilizará antes de consultar:

        - detalle
        - reflexiones
        - fallas
        - vacantes

        para impedir acceso a información
        de otros tutores.
        """

        return (
            db.query(AprendizPerfil)
            .filter(
                AprendizPerfil.tutor_id == tutor_id,
                AprendizPerfil.usuario_id == aprendiz_id,
            )
            .first()
            is not None
        )

    # ---------------------------------------------------------------------
    # Vacantes de un aprendiz (Paginadas)
    # ---------------------------------------------------------------------

    @staticmethod
    def get_apprentice_applications(
        db: Session,
        aprendiz_id: UUID,
        pagination: PaginationParams,
    ) -> list[Aplicacion]:
        """
        Recupera una página de aplicaciones
        pertenecientes a un aprendiz.

        Utilizado por el botón "Vacantes"
        del Dashboard del Tutor.
        """

        return (
            db.query(Aplicacion)
            .options(
                selectinload(
                    Aplicacion.entrevistas,
                ),
            )
            .filter(
                Aplicacion.usuario_id == aprendiz_id,
            )
            .order_by(
                Aplicacion.fecha_aplicacion.desc(),
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
    def count_apprentice_applications(
        db: Session,
        aprendiz_id: UUID,
    ) -> int:
        """
        Cantidad total de aplicaciones
        registradas por un aprendiz.

        Se utiliza para construir
        la paginación.
        """

        return (
            db.query(Aplicacion)
            .filter(
                Aplicacion.usuario_id == aprendiz_id,
            )
            .count()
        )
        # ---------------------------------------------------------------------
    # Reflexiones de un aprendiz (Paginadas)
    # ---------------------------------------------------------------------

    @staticmethod
    def get_apprentice_reflections(
        db: Session,
        aprendiz_id: UUID,
        pagination: PaginationParams,
    ) -> list[Entrevista]:
        """
        Recupera una página de entrevistas
        pertenecientes a un aprendiz.

        Se utiliza para construir la pestaña
        de Reflexiones del Dashboard del Tutor.
        """

        return (
            db.query(Entrevista)
            .options(
                selectinload(
                    Entrevista.aplicacion,
                ),
            )
            
            
            .join(Aplicacion)
            
            .filter(
                Aplicacion.usuario_id == aprendiz_id,
            )
            .order_by(
                Entrevista.fecha.desc(),
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
    def count_apprentice_reflections(
        db: Session,
        aprendiz_id: UUID,
    ) -> int:
        """
        Cantidad total de entrevistas
        registradas por un aprendiz.
        """

        return (
            db.query(Entrevista)
            .join(Aplicacion)
            .filter(
                Aplicacion.usuario_id == aprendiz_id,
            )
            .count()
        )
        
    # ---------------------------------------------------------------------
    # Fallas del aprendiz
    # ---------------------------------------------------------------------

    @staticmethod
    def get_apprentice_interviews(
        db: Session,
        aprendiz_id: UUID,
    ) -> list[Entrevista]:
        """
        Recupera todas las entrevistas de un aprendiz.

        Se utiliza para construir el Dashboard
        de Fallas.
        """

        return (
            db.query(Entrevista)
            .options(
                selectinload(
                    Entrevista.aplicacion,
                ),
            )
            .join(Aplicacion)
            .filter(
                Aplicacion.usuario_id == aprendiz_id,
            )
            .order_by(
                Entrevista.fecha.desc(),
            )
            .all()
        )