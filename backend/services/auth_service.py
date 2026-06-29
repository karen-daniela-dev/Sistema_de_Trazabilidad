#auth_service.py
from sqlalchemy.orm import Session

from backend.models.usuario import Usuario
from backend.models.enums import RolEnum
from backend.schemas import CohorteLoginResponse
from backend.services.tutor_dashboard_queries import (
    TutorDashboardQueries,
)


class AuthService:

    @staticmethod
    def build_login_cohort(
        db: Session,
        user: Usuario,
    ) -> CohorteLoginResponse | None:
        """
        Devuelve la cohorte que debe mostrarse
        después del inicio de sesión.
        """

        if user.rol == RolEnum.APRENDIZ:

            if not user.perfil:

                return None

            return CohorteLoginResponse(
                id=user.perfil.cohorte.id,
                nombre=user.perfil.cohorte.nombre,
            )

        if user.rol == RolEnum.TUTOR:

            cohorte = TutorDashboardQueries.get_tutor_cohorte(
                db,
                user.id,
            )

            if cohorte:

                return CohorteLoginResponse(
                    id=cohorte.id,
                    nombre=cohorte.nombre,
                )

        return None
