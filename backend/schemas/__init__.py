"""
schemas/__init__.py
Schemas Pydantic — validación de entrada y serialización de salida.
Separados de los modelos ORM para mantener independencia de capas.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional, List, Any

from pydantic import BaseModel, EmailStr, field_validator, model_validator

from backend.models.enums import (
    RolEnum, EstadoUsuario, EstadoCohorte,
    ModalidadApp, OrigenApp, EstadoApp,
    TipoEntrevista, ModalidadEntrevista, PercepcionGrupal,
    FallaEnum, TemaTecnico, RespuestaEmpresa,
    SUBFALLAS_POR_FALLA,
)
from backend.utils.security import validate_password_strength


# ── Auth ──────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    rol: RolEnum
    user_id: uuid.UUID


class ActivateAccountRequest(BaseModel):
    token: str
    password: str

    @field_validator("password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        validate_password_strength(v)
        return v


# ── Usuarios ──────────────────────────────────────────────────────────────────

class UsuarioBase(BaseModel):
    email: EmailStr
    rol: RolEnum


class RegistroAprendizRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        validate_password_strength(v)
        return v


class CrearTutorRequest(BaseModel):
    email: EmailStr


class UsuarioResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    email: str
    rol: RolEnum
    estado: EstadoUsuario
    activo: bool
    created_at: datetime
    last_login: Optional[datetime] = None


class UsuarioListResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    email: str
    rol: RolEnum
    estado: EstadoUsuario
    activo: bool
    created_at: datetime


# ── Cohortes ──────────────────────────────────────────────────────────────────

class CohorteCreate(BaseModel):
    nombre: str
    fecha_inicio: date
    meta_contratacion: int
    permitir_extension: bool = False

    @field_validator("meta_contratacion")
    @classmethod
    def meta_positiva(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("La meta de contratación debe ser mayor a 0.")
        return v


class CohorteUpdate(BaseModel):
    nombre: Optional[str] = None
    meta_contratacion: Optional[int] = None
    permitir_extension: Optional[bool] = None
    estado: Optional[EstadoCohorte] = None


class CohorteResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    nombre: str
    fecha_inicio: date
    fecha_fin: date
    estado: EstadoCohorte
    meta_contratacion: int
    permitir_extension: bool
    created_at: datetime


class CohorteListResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    nombre: str
    fecha_inicio: date
    fecha_fin: date
    estado: EstadoCohorte
    meta_contratacion: int
    permitir_extension: bool
    created_at: datetime


# ── Perfil Aprendiz ───────────────────────────────────────────────────────────

class PerfilAprendizCreate(BaseModel):
    cohorte_id: uuid.UUID
    tutor_id: uuid.UUID
    telefono: Optional[str] = None
    telefono_emergencia: Optional[str] = None
    ciudad: Optional[str] = None


class PerfilAprendizUpdate(BaseModel):
    """Aprendiz puede actualizar solo estos campos."""
    telefono: Optional[str] = None
    telefono_emergencia: Optional[str] = None
    ciudad: Optional[str] = None


class PerfilAprendizResponse(BaseModel):
    model_config = {"from_attributes": True}
    usuario_id: uuid.UUID
    cohorte_id: uuid.UUID
    tutor_id: uuid.UUID
    telefono: Optional[str] = None
    telefono_emergencia: Optional[str] = None
    ciudad: Optional[str] = None


class AlertaResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    target_id: uuid.UUID
    target_type: str
    mensaje: str
    leida: bool
    created_at: datetime


# ── Aplicaciones ──────────────────────────────────────────────────────────────

class AplicacionCreate(BaseModel):
    empresa: str
    vacante: str
    modalidad: ModalidadApp
    link: Optional[str] = None
    fecha_aplicacion: date = date.today()
    origen: OrigenApp

    @field_validator("empresa", "vacante")
    @classmethod
    def no_vacio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Este campo no puede estar vacío.")
        return v.strip()


class AplicacionResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    usuario_id: uuid.UUID
    empresa: str
    vacante: str
    modalidad: ModalidadApp
    link: Optional[str] = None
    fecha_aplicacion: date
    origen: OrigenApp
    estado: EstadoApp
    created_at: datetime
    updated_at: datetime


class AplicacionListResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    usuario_id: uuid.UUID
    empresa: str
    vacante: str
    modalidad: ModalidadApp
    fecha_aplicacion: date
    origen: OrigenApp
    estado: EstadoApp
    created_at: datetime


class MarcarContratadoRequest(BaseModel):
    aplicacion_id: uuid.UUID


# ── Entrevistas ───────────────────────────────────────────────────────────────

class EntrevistaCreate(BaseModel):
    aplicacion_id: uuid.UUID
    tipo: TipoEntrevista
    modalidad: ModalidadEntrevista
    fecha: datetime
    grupal: bool = False
    percepcion_grupal: Optional[PercepcionGrupal] = None
    fallas: List[FallaEnum] = []
    subfallas: List[str] = []
    temas_tecnicos: List[TemaTecnico] = []
    autoevaluacion: Optional[int] = None
    reflexion_bien: Optional[str] = None
    reflexion_mejorar: Optional[str] = None
    respuesta_empresa: Optional[RespuestaEmpresa] = None

    @model_validator(mode="after")
    def validar_condicionales(self) -> "EntrevistaCreate":
        # percepcion_grupal requerida si grupal == True
        if self.grupal and not self.percepcion_grupal:
            raise ValueError("percepcion_grupal es requerida cuando grupal=True.")

        # temas_tecnicos solo si TECNICA en fallas
        if self.temas_tecnicos and FallaEnum.TECNICA not in self.fallas:
            raise ValueError("temas_tecnicos solo aplica cuando TECNICA está en fallas.")

        # autoevaluacion entre 1 y 5
        if self.autoevaluacion is not None and not (1 <= self.autoevaluacion <= 5):
            raise ValueError("autoevaluacion debe estar entre 1 y 5.")

        

        return self


class EntrevistaResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    aplicacion_id: uuid.UUID
    tipo: TipoEntrevista
    modalidad: ModalidadEntrevista
    fecha: datetime
    grupal: bool
    percepcion_grupal: Optional[PercepcionGrupal] = None
    fallas: List[str] = []
    subfallas: List[str] = []
    temas_tecnicos: List[str] = []
    autoevaluacion: Optional[int] = None
    reflexion_bien: Optional[str] = None
    reflexion_mejorar: Optional[str] = None
    respuesta_empresa: Optional[RespuestaEmpresa] = None
    created_at: datetime
