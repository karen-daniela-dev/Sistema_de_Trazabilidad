import uuid
from datetime import date, datetime
from sqlalchemy import String, Boolean, Integer, Date, Enum as SAEnum, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base
from backend.models.enums import EstadoCohorte


class Cohorte(Base):
    __tablename__ = "cohortes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin: Mapped[date] = mapped_column(Date, nullable=False)  # calculado: inicio + 6 meses
    estado: Mapped[EstadoCohorte] = mapped_column(
        SAEnum(EstadoCohorte, name="estado_cohorte"),
        nullable=False,
        default=EstadoCohorte.ACTIVA,
    )
    meta_contratacion: Mapped[int] = mapped_column(Integer, nullable=False)
    permitir_extension: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relaciones
    aprendices: Mapped[list["AprendizPerfil"]] = relationship(
        "AprendizPerfil", back_populates="cohorte"
    )

    def __repr__(self) -> str:
        return f"<Cohorte {self.nombre} [{self.estado}]>"
