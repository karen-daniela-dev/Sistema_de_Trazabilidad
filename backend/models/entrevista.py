import uuid
from datetime import datetime
from sqlalchemy import (
    Boolean, SmallInteger, Text, DateTime, ForeignKey,
    Enum as SAEnum, func, Index
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base
from backend.models.enums import (
    TipoEntrevista, ModalidadEntrevista, PercepcionGrupal,
    FallaEnum, TemaTecnico, RespuestaEmpresa
)
#moels/entrevistas.py

class Entrevista(Base):
    __tablename__ = "entrevistas"
    __table_args__ = (
        Index("ix_entrevistas_aplicacion_fecha", "aplicacion_id", "fecha"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    aplicacion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("aplicaciones.id"), nullable=False, index=True
    )
    tipo: Mapped[TipoEntrevista] = mapped_column(
        SAEnum(TipoEntrevista, name="tipo_entrevista"), nullable=False
    )
    modalidad: Mapped[ModalidadEntrevista] = mapped_column(
        SAEnum(ModalidadEntrevista, name="modalidad_entrevista"), nullable=False
    )
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    grupal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Condicional: solo si grupal == True
    percepcion_grupal: Mapped[PercepcionGrupal | None] = mapped_column(
        SAEnum(PercepcionGrupal, name="percepcion_enum"), nullable=True
    )

    # Arrays de fallas y subfallas
    fallas: Mapped[list[str]] = mapped_column(ARRAY(SAEnum(FallaEnum, name="falla_enum")), default=list)
    subfallas: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)

    # Condicional: solo si TECNICA en fallas
    temas_tecnicos: Mapped[list[str]] = mapped_column(
        ARRAY(SAEnum(TemaTecnico, name="tema_tecnico_enum")), default=list
    )

    autoevaluacion: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    reflexion_bien: Mapped[str | None] = mapped_column(Text, nullable=True)
    reflexion_mejorar: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Sin impacto en lógica de estados
    respuesta_empresa: Mapped[RespuestaEmpresa | None] = mapped_column(
        SAEnum(RespuestaEmpresa, name="respuesta_empresa"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relaciones
    aplicacion: Mapped["Aplicacion"] = relationship("Aplicacion", back_populates="entrevistas")

    def __repr__(self) -> str:
        return f"<Entrevista {self.tipo} [{self.fecha}]>"
