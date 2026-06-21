import uuid
from datetime import date, datetime
from sqlalchemy import String, Text, Date, ForeignKey, Enum as SAEnum, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base
from backend.models.enums import ModalidadApp, OrigenApp, EstadoApp


class Aplicacion(Base):
    __tablename__ = "aplicaciones"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False, index=True
    )
    empresa: Mapped[str] = mapped_column(String(200), nullable=False)
    vacante: Mapped[str] = mapped_column(String(200), nullable=False)
    modalidad: Mapped[ModalidadApp] = mapped_column(
        SAEnum(ModalidadApp, name="modalidad_app"), nullable=False
    )
    link: Mapped[str | None] = mapped_column(Text, nullable=True)
    fecha_aplicacion: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    origen: Mapped[OrigenApp] = mapped_column(
        SAEnum(OrigenApp, name="origen_app"), nullable=False
    )
    # Estado calculado por el motor — NO editable por el usuario
    estado: Mapped[EstadoApp] = mapped_column(
        SAEnum(EstadoApp, name="estado_app"),
        nullable=False,
        default=EstadoApp.APLICADO,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relaciones
    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="aplicaciones")
    entrevistas: Mapped[list["Entrevista"]] = relationship(
        "Entrevista", back_populates="aplicacion", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Aplicacion {self.empresa} - {self.vacante} [{self.estado}]>"
