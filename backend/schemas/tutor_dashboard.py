#backend/schemas/tutor_dashboard.py

"""
schemas/tutor_dashboard.py

Schemas Pydantic exclusivos para el Dashboard del Tutor.

Estos DTOs representan la información consumida por el frontend
y NO corresponden directamente a las entidades ORM.

Objetivos:

- Desacoplar el frontend del modelo de base de datos.
- Facilitar la evolución del dashboard sin afectar los modelos.
- Reutilizar el sistema de paginación existente.
- Mantener compatibilidad con Pydantic v2.
"""

from __future__ import annotations

import uuid

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel

from backend.utils.pagination import Page


# =============================================================================
# ENUMS
# =============================================================================


class SemaforoEstado(str, Enum):
    """
    Estados de semáforo utilizados por el Dashboard del Tutor.

    IMPORTANTE:
    - VERDE, AMARILLO y ROJO pueden aplicarse tanto a
      actividad como a progreso.
    - INSUFFICIENT_DATA únicamente aplica al semáforo
      de progreso cuando todavía no existen suficientes
      aplicaciones maduras para realizar una evaluación.
    """

    VERDE = "GREEN"
    AMARILLO = "YELLOW"
    ROJO = "RED"

    # Solo utilizado por el semáforo de progreso
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
# =============================================================================
# BARRA DE META
# =============================================================================


class GoalProgressResponse(BaseModel):
    """
    Información utilizada por la barra superior
    de cumplimiento de meta.
    """

    model_config = {"from_attributes": True}

    porcentaje_meta: float
    porcentaje_actual: float
    porcentaje_cumplimiento: float

    total_aprendices: int

    meta_contratados: int

    contratados: int

    faltantes: int

    sobrecumplimiento: int

    meta_alcanzada: bool

    sobrecumplida: bool


# =============================================================================
# TARJETAS SUPERIORES
# =============================================================================


class SummaryCardsResponse(BaseModel):
    """
    Tarjetas resumen mostradas en la parte superior
    del dashboard.
    """

    model_config = {"from_attributes": True}

    total_aprendices: int

    contratados: int

    tasa_contratacion: float

    actividad_promedio: float

    progreso_promedio: float
    
# =============================================================================
# RESUMEN DEL DASHBOARD
# =============================================================================


class TutorSummaryResponse(BaseModel):
    """
    Respuesta completa del encabezado del Dashboard.

    Contiene:

    - Barra de cumplimiento de meta.
    - Tarjetas de indicadores.
    """

    model_config = {"from_attributes": True}

    goal: GoalProgressResponse

    cards: SummaryCardsResponse


# =============================================================================
# TABLA PRINCIPAL DE APRENDICES
# =============================================================================


class TutorApprenticeRowResponse(BaseModel):
    """
    Representa una fila de la tabla principal
    del Dashboard del Tutor.
    """

    model_config = {"from_attributes": True}

    id: uuid.UUID

    nombre: str

    email: str

    telefono: Optional[str] = None

    telefono_emergencia: Optional[str] = None

    ciudad: Optional[str] = None

    total_aplicaciones: int

    actividad: SemaforoEstado

    progreso: SemaforoEstado

    contratado: bool

    ultima_actividad: Optional[datetime] = None


# Alias reutilizable para la tabla paginada

TutorApprenticePage = Page[TutorApprenticeRowResponse]


# =============================================================================
# DETALLE DEL APRENDIZ
# =============================================================================


class TutorApprenticeDetailResponse(BaseModel):
    """
    Información básica mostrada cuando
    el tutor selecciona un aprendiz.

    No incluye aplicaciones,
    entrevistas,
    fallas
    ni reflexiones.
    """

    model_config = {"from_attributes": True}

    id: uuid.UUID

    nombre: str

    email: str

    telefono: Optional[str] = None

    telefono_emergencia: Optional[str] = None

    ciudad: Optional[str] = None

    actividad: SemaforoEstado

    progreso: SemaforoEstado

    contratado: bool

    total_aplicaciones: int

    total_entrevistas: int

    ultima_aplicacion: Optional[datetime] = None

    ultima_entrevista: Optional[datetime] = None
    
    
# =============================================================================
# ALERTAS
# =============================================================================


class TutorAlertResponse(BaseModel):
    """
    Representa una alerta mostrada en la pestaña
    de Alertas del Dashboard del Tutor.
    """

    model_config = {"from_attributes": True}

    id: uuid.UUID

    aprendiz_id: uuid.UUID

    nombre_aprendiz: str

    actividad: SemaforoEstado

    progreso: SemaforoEstado

    prioridad: int

    tipo: str

    mensaje: str

    created_at: datetime


TutorAlertPage = Page[TutorAlertResponse]


# =============================================================================
# RESUMEN DE FALLAS
# =============================================================================
# =============================================================================
# RESUMEN DE FALLAS
# =============================================================================


class FailureSliceResponse(BaseModel):
    """
    Elemento mostrado dentro de una torta.

    Dependiendo de la categoría puede representar:

    - una subfalla
    - un tema técnico
    """

    model_config = {"from_attributes": True}

    nombre: str

    cantidad: int

    porcentaje: float


class FailurePieResponse(BaseModel):
    """
    Representa una torta del Dashboard
    de fallas.

    Existe una torta por cada categoría
    de falla.
    """

    model_config = {"from_attributes": True}

    falla: str

    titulo: str

    total: int

    elementos: list[FailureSliceResponse]


class TutorFailureSummaryResponse(BaseModel):
    """
    Información necesaria para construir
    todas las tortas del Dashboard
    de Fallas.
    """

    model_config = {"from_attributes": True}

    total_entrevistas: int

    pies: list[FailurePieResponse]




    
# =============================================================================
# REFLEXIONES
# =============================================================================


class TutorReflectionResponse(BaseModel):
    """
    Reflexión registrada en una entrevista.

    Se utiliza en el panel "Ver reflexiones"
    del Dashboard del Tutor.
    """

    model_config = {"from_attributes": True}

    entrevista_id: uuid.UUID

    fecha: datetime

    empresa: str

    vacante: str

    tipo_entrevista: str

    reflexion_bien: Optional[str] = None

    reflexion_mejorar: Optional[str] = None

    autoevaluacion: Optional[int] = None


TutorReflectionPage = Page[TutorReflectionResponse]


# =============================================================================
# VACANTES DEL APRENDIZ
# =============================================================================


class TutorApplicationResponse(BaseModel):
    """
    Vacantes mostradas cuando el tutor
    consulta el detalle de un aprendiz.

    La información es muy similar a la del
    Dashboard del Aprendiz, pero desacoplada
    del dominio para mantener independencia
    entre ambos módulos.
    """

    model_config = {"from_attributes": True}

    id: uuid.UUID

    empresa: str

    vacante: str

    modalidad: str

    origen: str

    estado: str

    fecha_aplicacion: datetime

    total_entrevistas: int

    contratado: bool


TutorApplicationPage = Page[TutorApplicationResponse]


# =============================================================================
# FILTROS DE LA TABLA PRINCIPAL
# =============================================================================


class TutorApprenticeFilters(BaseModel):
    """
    Filtros utilizados por el endpoint
    de la tabla principal.

    Todos los campos son opcionales.
    """

    nombre: Optional[str] = None

    actividad: Optional[SemaforoEstado] = None

    progreso: Optional[SemaforoEstado] = None

    contratado: Optional[bool] = None

    ciudad: Optional[str] = None