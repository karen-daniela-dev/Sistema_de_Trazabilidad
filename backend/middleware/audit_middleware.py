"""
Middleware de auditoría — registra acciones críticas en audit_logs.
Se usa como función helper desde los routers, no como middleware HTTP
(para tener acceso a la sesión DB).
"""
import logging
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from backend.models.audit_log import AuditLog

logger = logging.getLogger(__name__)

ACCIONES_CRITICAS = {
    "LOGIN", "LOGIN_FAILED", "LOGOUT",
    "REGISTER_APRENDIZ", "REGISTER_TUTOR", "ACTIVATE_TUTOR",
    "CREATE_APLICACION", "DELETE_APLICACION",
    "CREATE_ENTREVISTA",
    "MARCAR_CONTRATADO",
    "CREATE_COHORTE", "UPDATE_COHORTE",
    "UPDATE_PERFIL",
    "CAMBIO_ROL", "DESACTIVAR_USUARIO",
}


def registrar(
    db: Session,
    accion: str,
    usuario_id: UUID | None = None,
    detalle: dict[str, Any] | None = None,
    ip: str | None = None,
) -> None:
    """
    Registra una acción en audit_logs.
    Solo almacena acciones definidas en ACCIONES_CRITICAS.
    """
    if accion not in ACCIONES_CRITICAS:
        logger.warning("Acción no reconocida para auditoría: %s", accion)
        return

    log = AuditLog(
        usuario_id=usuario_id,
        accion=accion,
        detalle=detalle,
        ip=ip,
    )
    db.add(log)
    # No hace commit — el router es responsable del commit de la transacción completa
