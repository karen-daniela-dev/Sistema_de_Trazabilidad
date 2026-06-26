import uuid
from sqlalchemy import String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base

#models/aprendiz_perfil.py


class AprendizPerfil(Base):
    __tablename__ = "aprendiz_perfil"

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id"), primary_key=True
    )
    telefono: Mapped[str | None] = mapped_column(String(20), nullable=True)
    telefono_emergencia: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ciudad: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cohorte_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cohortes.id"), nullable=False
    )
    tutor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False
    )

    # Relaciones
    usuario: Mapped["Usuario"] = relationship(
        "Usuario", back_populates="perfil", foreign_keys=[usuario_id]
    )
    cohorte: Mapped["Cohorte"] = relationship("Cohorte", back_populates="aprendices")
    tutor: Mapped["Usuario"] = relationship(
        "Usuario", back_populates="tutores_asignados", foreign_keys=[tutor_id]
    )

    def __repr__(self) -> str:
        return f"<AprendizPerfil {self.usuario_id}>"
