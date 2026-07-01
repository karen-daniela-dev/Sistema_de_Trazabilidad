"""
backend/dependencies/auth.py
Dependencias FastAPI — inyección de sesión DB y usuario autenticado.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.usuario import Usuario
from backend.models.enums import RolEnum
from backend.utils.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No autenticado o token inválido.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        if not user_id:
            raise credentials_exc
    except JWTError:
        raise credentials_exc

    user = db.query(Usuario).filter(Usuario.id == user_id, Usuario.activo == True).first()
    if not user:
        raise credentials_exc
    return user


def require_roles(*roles: RolEnum):
    """
    Fábrica de dependencias — restringe endpoint a los roles indicados.
    Uso: Depends(require_roles(RolEnum.COORDINADOR, RolEnum.TUTOR))
    """
    def checker(current_user: Usuario = Depends(get_current_user)) -> Usuario:
        if current_user.rol not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado. Roles permitidos: {[r.value for r in roles]}",
            )
        return current_user
    return checker


# Shortcuts
require_coordinador = require_roles(RolEnum.COORDINADOR)
require_tutor = require_roles(RolEnum.TUTOR, RolEnum.COORDINADOR)
require_aprendiz = require_roles(RolEnum.APRENDIZ)
require_any = require_roles(RolEnum.COORDINADOR, RolEnum.TUTOR, RolEnum.APRENDIZ)
