import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, Enum as SAEnum, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base
from backend.models.enums import RolEnum, EstadoUsuario
#models/usuario.py

class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    rol: Mapped[RolEnum] = mapped_column(SAEnum(RolEnum, name="rol_enum"), nullable=False, index=True)
    estado: Mapped[EstadoUsuario] = mapped_column(
        SAEnum(EstadoUsuario, name="estado_usuario"),
        nullable=False,
        default=EstadoUsuario.PENDIENTE,
    )
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relaciones
    perfil: Mapped["AprendizPerfil"] = relationship(
        "AprendizPerfil", 
        foreign_keys="[AprendizPerfil.usuario_id]",
        back_populates="usuario", 
        uselist=False, 
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    aplicaciones: Mapped[list["Aplicacion"]] = relationship(
        "Aplicacion", back_populates="usuario", cascade="all, delete-orphan", lazy="selectin"
    )
    tutores_asignados: Mapped[list["AprendizPerfil"]] = relationship(
        "AprendizPerfil",
        foreign_keys="[AprendizPerfil.tutor_id]",
        back_populates="tutor",
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", back_populates="usuario", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Usuario {self.email} [{self.rol}]>"
