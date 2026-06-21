"""
Utilidades de seguridad:
- Hashing bcrypt de contraseñas
- Generación y verificación de JWT
- Políticas de contraseñas fuertes
"""
import re
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── Password ──────────────────────────────────────────────────────────────────

_PASSWORD_RE = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&\-_])[A-Za-z\d@$!%*?&\-_]{8,}$"
)


def validate_password_strength(password: str) -> None:
    """
    Lanza ValueError si la contraseña no cumple la política:
    - Mínimo 8 caracteres
    - Al menos 1 mayúscula, 1 minúscula, 1 dígito, 1 carácter especial
    """
    if not _PASSWORD_RE.match(password):
        raise ValueError(
            "La contraseña debe tener mínimo 8 caracteres, "
            "una mayúscula, una minúscula, un número y un carácter especial (@$!%*?&-_)."
        )


def hash_password(password: str) -> str:
    validate_password_strength(password)
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── JWT ───────────────────────────────────────────────────────────────────────

def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """
    Decodifica y valida el token JWT.
    Lanza JWTError si es inválido o expirado.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
