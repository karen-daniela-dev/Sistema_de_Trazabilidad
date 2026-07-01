"""
services/tutor_dashboard_service.py

Servicio principal del Dashboard del Tutor.

Responsabilidades:

- Orquestar consultas.
- Reutilizar la lógica existente de KPIs.
- Construir los DTOs del Dashboard.
- No ejecutar consultas SQL directamente.
"""

from __future__ import annotations


from uuid import UUID

from backend.constants.interview_catalog import FALLAS, get_falla_from_subfalla
from backend.models import usuario
from backend.services.kpi_helpers import collect_user_entrevistas
from backend.services.user_helpers import display_name
from sqlalchemy.orm import Session

from backend.schemas.tutor_dashboard import (
    FailurePieResponse,
    FailureSliceResponse,
    GoalProgressResponse,
    SummaryCardsResponse,
    TutorApplicationPage,
    TutorApplicationResponse,
    TutorApprenticeDetailResponse,
    TutorFailureSummaryResponse,
    TutorReflectionPage,
    TutorReflectionResponse,
    TutorSummaryResponse,
    TutorApprenticeRowResponse,
    SemaforoEstado,
    TutorApprenticePage,
)

from backend.models.enums import EstadoApp

from backend.services.kpi_service import (
    build_user_kpi,
  
    load_apps_and_entrevistas_for_users,
)

from backend.services.tutor_dashboard_queries import TutorDashboardQueries
from datetime import datetime, UTC
from backend.models.aplicacion import Aplicacion
from backend.models.entrevista import Entrevista
from backend.models.usuario import Usuario
from backend.models.aprendiz_perfil import AprendizPerfil
from backend.utils.pagination import (
    PaginationParams,
)


class TutorDashboardService:
    """
    Servicio principal del Dashboard Tutor.

    Este servicio reutiliza las reglas del Dashboard
    del Aprendiz para garantizar consistencia entre
    ambos módulos.
    """

    # ------------------------------------------------------------------
    # Dashboard superior
    # ------------------------------------------------------------------
    @staticmethod
    def get_summary(
        db: Session,
        tutor_id: UUID,
    ) -> TutorSummaryResponse:
        """
        Construye el encabezado del Dashboard del Tutor.

        Incluye:

        - Barra de cumplimiento de meta.
        - Tarjetas superiores.

        No calcula semáforos ni KPIs individuales.
        """


        cohorte = TutorDashboardQueries.get_tutor_cohorte(
            db,
            tutor_id,
        )

        if cohorte is None:

            return TutorSummaryResponse(
                goal=GoalProgressResponse(
                    porcentaje_meta=0,
                    porcentaje_actual=0,
                    porcentaje_cumplimiento=0,
                    total_aprendices=0,
                    meta_contratados=0,
                    contratados=0,
                    faltantes=0,
                    sobrecumplimiento=0,
                    meta_alcanzada=False,
                    sobrecumplida=False,
                ),
                cards=SummaryCardsResponse(
                    total_aprendices=0,
                    contratados=0,
                    tasa_contratacion=0,
                    actividad_promedio=0,
                    progreso_promedio=0,
                ),
            )

        perfiles = TutorDashboardQueries.get_apprentices(
            db,
            tutor_id,
            cohorte.id,
        ) 
        #-----       

        total_aprendices = len(perfiles)

        if total_aprendices == 0:

            return TutorSummaryResponse(
                goal=GoalProgressResponse(
                    porcentaje_meta=0,
                    porcentaje_actual=0,
                    porcentaje_cumplimiento=0,
                    total_aprendices=0,
                    meta_contratados=0,
                    contratados=0,
                    faltantes=0,
                    sobrecumplimiento=0,
                    meta_alcanzada=False,
                    sobrecumplida=False,
                ),
                cards=SummaryCardsResponse(
                    total_aprendices=0,
                    contratados=0,
                    tasa_contratacion=0,
                    actividad_promedio=0,
                    progreso_promedio=0,
                ),
            )

        usuarios_ids = [
            perfil.usuario_id
            for perfil in perfiles
        ]

        apps_by_user, _ = load_apps_and_entrevistas_for_users(
            db,
            usuarios_ids,
        )

        contratados = sum(
            1
            for apps in apps_by_user.values()
            if any(
                app.estado == EstadoApp.CONTRATADO
                for app in apps
            )
        )

       
        print("Tutorrrr:", tutor_id)
        print("Cohorte:", cohorte.id if cohorte else None)
        print("Meta:", cohorte.meta_contratacion if cohorte else None)

        porcentaje_meta = (
            cohorte.meta_contratacion
            if cohorte
            else 0
        )

        meta_contratados = round(
            total_aprendices * porcentaje_meta / 100
        )

        porcentaje_actual = (
            (contratados / total_aprendices) * 100
            if total_aprendices
            else 0
        )

        porcentaje_cumplimiento = (
            (contratados / meta_contratados) * 100
            if meta_contratados
            else 0
        )

        faltantes = max(
            0,
            meta_contratados - contratados,
        )

        sobrecumplimiento = max(
            0,
            contratados - meta_contratados,
        )

        return TutorSummaryResponse(

            goal=GoalProgressResponse(

                porcentaje_meta=porcentaje_meta,

                porcentaje_actual=round(
                    porcentaje_actual,
                    2,
                ),

                porcentaje_cumplimiento=round(
                    porcentaje_cumplimiento,
                    2,
                ),

                total_aprendices=total_aprendices,

                meta_contratados=meta_contratados,

                contratados=contratados,

                faltantes=faltantes,

                sobrecumplimiento=sobrecumplimiento,

                meta_alcanzada=contratados >= meta_contratados,

                sobrecumplida=sobrecumplimiento > 0,
            ),

            cards=SummaryCardsResponse(

                total_aprendices=total_aprendices,

                contratados=contratados,

                tasa_contratacion=round(
                    porcentaje_actual,
                    2,
                ),

                # Estas dos tarjetas no se utilizarán
                # en la primera versión del Dashboard.
                actividad_promedio=0,

                progreso_promedio=0,
            ),
        )
        
        
        
    @staticmethod
    def _build_apprentice_detail(
        db: Session,
        perfil: AprendizPerfil,
    ) -> TutorApprenticeDetailResponse:
        """
        Construye el detalle de un aprendiz a partir
        de su perfil.

        No realiza validaciones de permisos.
        """

        aprendiz_id = perfil.usuario_id

        apps_by_user, entrevistas_by_app = (
            load_apps_and_entrevistas_for_users(
                db,
                [aprendiz_id],
            )
        )

        aplicaciones = apps_by_user.get(
            aprendiz_id,
            [],
        )

        entrevistas = collect_user_entrevistas(
            aplicaciones,
            entrevistas_by_app,
        )

        kpi = build_user_kpi(
            aplicaciones,
            entrevistas,
        )

        ultima_aplicacion = max(
            (a.fecha_aplicacion for a in aplicaciones),
            default=None,
        )

        ultima_entrevista = max(
            (e.fecha for e in entrevistas),
            default=None,
        )

        usuario = perfil.usuario

        if usuario is None:
            raise ValueError(
                "El perfil del aprendiz no tiene un usuario asociado."
            )

        return TutorApprenticeDetailResponse(

            id=usuario.id,

            nombre=display_name(usuario),

            email=usuario.email,

            telefono=perfil.telefono,

            telefono_emergencia=perfil.telefono_emergencia,

            ciudad=perfil.ciudad,

            actividad=SemaforoEstado(
                kpi["semaforo_actividad"],
            ),

            progreso=SemaforoEstado(
                kpi["semaforo_progreso"],
            ),

            contratado=kpi["contratado"],

            total_aplicaciones=kpi["total_aplicaciones"],

            total_entrevistas=kpi["total_entrevistas"],

            ultima_aplicacion=ultima_aplicacion,

            ultima_entrevista=ultima_entrevista,
        )
    # Métodos privados reutilizables
    @staticmethod
    def _calculate_last_activity(
        apps: list[Aplicacion],
        entrevistas: list[Entrevista],
    ) -> datetime | None:
        """
        Obtiene la fecha de la última actividad del aprendiz.

        Se consideran como actividad:

        - Fecha de aplicación a una vacante.
        - Fecha de entrevista.

        Retorna None cuando el aprendiz aún no registra
        aplicaciones ni entrevistas.
        """

        fechas: list[datetime] = []

        for app in apps:
            if app.fecha_aplicacion:
                fechas.append(
                    datetime.combine(
                        app.fecha_aplicacion,
                        datetime.min.time(),
                        tzinfo=UTC,
                    )
                )

        for entrevista in entrevistas:
            if entrevista.fecha:
                fechas.append(entrevista.fecha)

        if not fechas:
            return None

        return max(fechas)
    @staticmethod
    def _map_semaforo(
        value: str,
    ) -> SemaforoEstado:
        """
        Convierte el valor retornado por el motor de KPIs
        al enum utilizado por el Dashboard del Tutor.
        """

        mapping = {
            "GREEN": SemaforoEstado.VERDE,
            "YELLOW": SemaforoEstado.AMARILLO,
            "RED": SemaforoEstado.ROJO,
            "INSUFFICIENT_DATA": SemaforoEstado.INSUFFICIENT_DATA,
        }

        return mapping.get(
            value,
            SemaforoEstado.ROJO,
        )
   
    
    @staticmethod
    def _build_apprentice_row(
        perfil: AprendizPerfil,
        apps: list[Aplicacion],
        entrevistas: list[Entrevista],
    ) -> TutorApprenticeRowResponse:
        """
        Construye una fila de la tabla principal del
        Dashboard del Tutor.

        No realiza consultas SQL.
        Reutiliza el motor de KPIs del sistema.
        """

        usuario = perfil.usuario

        if usuario is None:
            raise ValueError(
                "El perfil del aprendiz no tiene un usuario asociado."
            )

        kpi = build_user_kpi(
            apps,
            entrevistas,
        )

        return TutorApprenticeRowResponse(

            id=usuario.id,

            nombre=display_name(usuario),
            

            email=usuario.email,

            telefono=perfil.telefono,

            telefono_emergencia=perfil.telefono_emergencia,

            ciudad=perfil.ciudad,

            total_aplicaciones=kpi["total_aplicaciones"],

            actividad=TutorDashboardService._map_semaforo(
                kpi["semaforo_actividad"],
            ),

            progreso=TutorDashboardService._map_semaforo(
                kpi["semaforo_progreso"],
            ),

            contratado=kpi["contratado"],

            ultima_actividad=TutorDashboardService._calculate_last_activity(
                apps,
                entrevistas,
            ),
        )
        
        
    @staticmethod
    def _sort_rows(
        rows: list[TutorApprenticeRowResponse],
        sort_by: str,
        descending: bool,
    ) -> list[TutorApprenticeRowResponse]:
        """
        Ordena las filas de la tabla principal.
        """

        actividad_order = {
            SemaforoEstado.ROJO: 0,
            SemaforoEstado.AMARILLO: 1,
            SemaforoEstado.VERDE: 2,
        }

        progreso_order = {
            SemaforoEstado.ROJO: 0,
            SemaforoEstado.AMARILLO: 1,
            SemaforoEstado.INSUFFICIENT_DATA: 2,
            SemaforoEstado.VERDE: 3,
        }

        if sort_by == "actividad":

            return sorted(
                rows,
                key=lambda row: actividad_order[row.actividad],
                reverse=descending,
            )

        if sort_by == "progreso":

            return sorted(
                rows,
                key=lambda row: progreso_order[row.progreso],
                reverse=descending,
            )

        if sort_by == "nombre":

            return sorted(
                rows,
                key=lambda row: row.nombre.lower(),
                reverse=descending,
            )

        if sort_by == "vacantes":

            return sorted(
                rows,
                key=lambda row: row.total_aplicaciones,
                reverse=descending,
            )

        if sort_by == "contratado":

            return sorted(
                rows,
                key=lambda row: row.contratado,
                reverse=descending,
            )

        return rows
    
    @staticmethod
    def _paginate_rows(
        rows: list[TutorApprenticeRowResponse],
        pagination: PaginationParams,
    ) -> TutorApprenticePage:
        """
        Aplica paginación sobre una colección de filas.
        """

        total = len(rows)

        start = pagination.offset
        end = start + pagination.size

        return TutorApprenticePage.build(
            items=rows[start:end],
            total=total,
            params=pagination,
        )       
        
    @staticmethod
    def get_apprentices_page(
        db: Session,
        tutor_id: UUID,
        pagination: PaginationParams,
        search: str | None = None,
        actividad: SemaforoEstado | None = None,
        progreso: SemaforoEstado | None = None,
        contratado: bool | None = None,
        sort_by: str = "actividad",
        descending: bool = False,
    ) -> TutorApprenticePage:
        """
        Obtiene la tabla principal del Dashboard del Tutor.
        """
        cohorte = TutorDashboardQueries.get_tutor_cohorte(
            db,
            tutor_id,
        )

        if cohorte is None:

            return TutorDashboardService._paginate_rows(
                [],
                pagination,
            )

        perfiles = TutorDashboardQueries.get_apprentices(
            db,
            tutor_id,
            cohorte.id,
        )
       

        usuarios_ids = [
            perfil.usuario_id
            for perfil in perfiles
        ]

        apps_by_user, entrevistas_by_app = (
            load_apps_and_entrevistas_for_users(
                db,
                usuarios_ids,
            )
        )

        rows: list[TutorApprenticeRowResponse] = []

        for perfil in perfiles:

            apps = apps_by_user.get(
                perfil.usuario_id,
                [],
            )

            entrevistas: list[Entrevista] = []

            for app in apps:
                entrevistas.extend(
                    entrevistas_by_app.get(
                        app.id,
                        [],
                    )
                )

            rows.append(
                TutorDashboardService._build_apprentice_row(
                    perfil,
                    apps,
                    entrevistas,
                )
            )   
        # ----------------------------------------------------------
        # Búsqueda
        # ----------------------------------------------------------

        if search:

            search = search.strip().lower()

            rows = [
                row
                for row in rows
                if (
                    search in row.nombre.lower()
                    or search in row.email.lower()
                )
            ]

        # ----------------------------------------------------------
        # Filtros
        # ----------------------------------------------------------

        if actividad is not None:

            rows = [
                row
                for row in rows
                if row.actividad == actividad
            ]

        if progreso is not None:

            rows = [
                row
                for row in rows
                if row.progreso == progreso
            ]

        if contratado is not None:

            rows = [
                row
                for row in rows
                if row.contratado == contratado
            ]
        # ----------------------------------------------------------
        # Ordenamiento
        # ----------------------------------------------------------

        rows = TutorDashboardService._sort_rows(
            rows,
            sort_by,
            descending,
        )
        # ----------------------------------------------------------
        # Paginación
        # ----------------------------------------------------------

        return TutorDashboardService._paginate_rows(
            rows,
            pagination,
        )
        
    @staticmethod
    def get_apprentice_detail(
        db: Session,
        tutor_id: UUID,
        aprendiz_id: UUID,
    ) -> TutorApprenticeDetailResponse:
        """
        Obtiene la información general de un aprendiz.
        """

        perfil = TutorDashboardQueries.get_aprendiz(
            db,
            aprendiz_id,
            tutor_id=tutor_id,
        )

        if perfil is None:
            raise ValueError(
                "El aprendiz no pertenece al tutor."
            )

        return TutorDashboardService._build_apprentice_detail(
            db,
            perfil,
        )
        
        

        
    @staticmethod
    def get_applications(
        db: Session,
        tutor_id: UUID,
        aprendiz_id: UUID,
        pagination: PaginationParams,
    ) -> TutorApplicationPage:
        """
        Obtiene las aplicaciones de un aprendiz
        perteneciente al tutor autenticado.
        """

        if not TutorDashboardQueries.aprendiz_belongs_to_tutor(
            db,
            tutor_id,
            aprendiz_id,
        ):
            raise ValueError(
                "El aprendiz no pertenece al tutor."
            )

        aplicaciones = (
            TutorDashboardQueries.get_apprentice_applications(
                db,
                aprendiz_id,
                pagination,
            )
        )

        total = (
            TutorDashboardQueries.count_apprentice_applications(
                db,
                aprendiz_id,
            )
        )

        rows: list[TutorApplicationResponse] = []

        for app in aplicaciones:

            rows.append(

                TutorApplicationResponse(

                    id=app.id,

                    empresa=app.empresa,

                    vacante=app.vacante,

                    modalidad=app.modalidad,

                    origen=app.origen,

                    estado=app.estado.value,

                    fecha_aplicacion=app.fecha_aplicacion,

                    total_entrevistas=len(
                        app.entrevistas,
                    ),

                    contratado=(
                        app.estado
                        == EstadoApp.CONTRATADO
                    ),
                )
            )

        return TutorApplicationPage.build(

            items=rows,

            total=total,

            params=pagination,
        )
    @staticmethod
    def get_reflections(
        db: Session,
        tutor_id: UUID,
        aprendiz_id: UUID,
        pagination: PaginationParams,
    ) -> TutorReflectionPage:
        """
        Obtiene las reflexiones registradas
        durante las entrevistas de un aprendiz.
        """

        if not TutorDashboardQueries.aprendiz_belongs_to_tutor(
            db,
            tutor_id,
            aprendiz_id,
        ):
            raise ValueError(
                "El aprendiz no pertenece al tutor."
            )

        entrevistas = (
            TutorDashboardQueries.get_apprentice_reflections(
                db,
                aprendiz_id,
                pagination,
            )
        )

        total = (
            TutorDashboardQueries.count_apprentice_reflections(
                db,
                aprendiz_id,
            )
        )

        rows: list[TutorReflectionResponse] = []

        for entrevista in entrevistas:

            rows.append(

                TutorReflectionResponse(

                    entrevista_id=entrevista.id,

                    fecha=entrevista.fecha,

                    empresa=entrevista.aplicacion.empresa,

                    vacante=entrevista.aplicacion.vacante,

                    tipo_entrevista=entrevista.tipo.value,

                    reflexion_bien=entrevista.reflexion_bien,

                    reflexion_mejorar=entrevista.reflexion_mejorar,

                    autoevaluacion=entrevista.autoevaluacion,
                )
            )

        return TutorReflectionPage.build(
            items=rows,
            total=total,
            params=pagination,
        )
    @staticmethod
    def _build_failure_summary(
        db: Session,
        aprendiz_id: UUID,
    ) -> TutorFailureSummaryResponse:
        """
        Construye las tortas de fallas de un aprendiz.

        No realiza validaciones de permisos.
        Puede reutilizarse desde distintos dashboards.
        """

        entrevistas = (
            TutorDashboardQueries.get_apprentice_interviews(
                db,
                aprendiz_id,
            )
        )

        if not entrevistas:

            pies: list[FailurePieResponse] = []

            for falla, titulo in FALLAS.items():

                pies.append(

                    FailurePieResponse(

                        falla=falla,

                        titulo=titulo,

                        total=0,

                        elementos=[],
                    )
                )

            return TutorFailureSummaryResponse(

                total_entrevistas=0,

                pies=pies,
            )

        pies: list[FailurePieResponse] = []

        total_entrevistas = len(
            entrevistas,
        )

        for falla, titulo in FALLAS.items():

            contador: dict[str, int] = {}

            for entrevista in entrevistas:

                # ------------------------------------------------------
                # Subfallas
                # ------------------------------------------------------

                for subfalla in entrevista.subfallas or []:

                    categoria = get_falla_from_subfalla(
                        subfalla,
                    )

                    if categoria is None:
                        continue

                    if categoria != falla:
                        continue

                    contador[subfalla] = (
                        contador.get(
                            subfalla,
                            0,
                        )
                        + 1
                    )

                # ------------------------------------------------------
                # Temas técnicos
                # ------------------------------------------------------

                if (
                    falla == "TECNICA"
                    and "TECNICA" in (entrevista.fallas or [])
                ):

                    for tema in entrevista.temas_tecnicos or []:

                        contador[tema] = (
                            contador.get(
                                tema,
                                0,
                            )
                            + 1
                        )

            total = sum(
                contador.values(),
            )

            elementos: list[FailureSliceResponse] = []

            if total > 0:

                for nombre, cantidad in sorted(
                    contador.items(),
                    key=lambda item: (-item[1], item[0]),
                ):

                    elementos.append(

                        FailureSliceResponse(

                            nombre=nombre,

                            cantidad=cantidad,

                            porcentaje=round(
                                (cantidad / total) * 100,
                                2,
                            ),
                        )
                    )

            pies.append(

                FailurePieResponse(

                    falla=falla,

                    titulo=titulo,

                    total=total,

                    elementos=elementos,
                )
            )

        return TutorFailureSummaryResponse(

            total_entrevistas=total_entrevistas,

            pies=pies,
        )


    @staticmethod
    def get_failure_summary(
        db: Session,
        tutor_id: UUID,
        aprendiz_id: UUID,
    ) -> TutorFailureSummaryResponse:
        """
        Construye las tortas de fallas de un aprendiz.
        """

        if not TutorDashboardQueries.aprendiz_belongs_to_tutor(
            db,
            tutor_id,
            aprendiz_id,
        ):
            raise ValueError(
                "El aprendiz no pertenece al tutor."
            )

        return TutorDashboardService._build_failure_summary(
            db,
            aprendiz_id,
        )
            

        
        
        
    