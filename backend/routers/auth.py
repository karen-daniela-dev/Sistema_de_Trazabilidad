"""
Router de autenticación:
- POST /auth/register     → registro de aprendiz
- POST /auth/login        → login JWT
- POST /auth/activate     → activación de tutor (establece contraseña)
- GET  /auth/me           → usuario actual
"""
from datetime import datetime, timezone

from backend.services.auth_service import AuthService
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies.auth import get_current_user
from backend.middleware.audit_middleware import registrar
from backend.models.enums import EstadoUsuario, RolEnum, EstadoCohorte
from backend.models.usuario import Usuario
from backend.schemas import (
    TokenResponse, RegistroAprendizRequest,
    ActivateAccountRequest, UsuarioResponse,
)
from backend.utils.security import (
    hash_password, verify_password, create_access_token,
)

router = APIRouter(prefix="/auth", tags=["Autenticación"])


def _get_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    return forwarded.split(",")[0] if forwarded else request.client.host


@router.post("/register", response_model=UsuarioResponse, status_code=201)
def register_aprendiz(payload: RegistroAprendizRequest, request: Request, db: Session = Depends(get_db)):
    """Registro de aprendiz. Estado inicial: ACTIVO."""
    if db.query(Usuario).filter(Usuario.email == payload.email).first():
        raise HTTPException(status_code=400, detail="El email ya está registrado.")

    user = Usuario(
        email=payload.email,
        password_hash=hash_password(payload.password),
        rol=RolEnum.APRENDIZ,
        estado=EstadoUsuario.ACTIVO,
        activo=True,
    )
    db.add(user)
    db.flush()
    registrar(db, "REGISTER_APRENDIZ", usuario_id=user.id,
              detalle={"email": user.email}, ip=_get_ip(request))
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None,
    db: Session = Depends(get_db),
):
    """
    Login estándar OAuth2. Rate-limiting aplicado en main.py.
    Verifica estado de cohorte para aprendices.
    """
    user = db.query(Usuario).filter(
        Usuario.email == form_data.username,
        Usuario.activo == True,
    ).first()

    if not user or not verify_password(form_data.password, user.password_hash):
        registrar(db, "LOGIN_FAILED",
                  detalle={"email": form_data.username}, ip=_get_ip(request))
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.estado == EstadoUsuario.PENDIENTE:
        raise HTTPException(status_code=403, detail="Cuenta pendiente de activación.")

    # Bloquear aprendiz si su cohorte está FINALIZADA y no tiene extensión
    if user.rol == RolEnum.APRENDIZ and user.perfil:
        cohorte = user.perfil.cohorte
        if cohorte and cohorte.estado == EstadoCohorte.FINALIZADA and not cohorte.permitir_extension:
            raise HTTPException(status_code=403, detail="Cohorte finalizada. Acceso bloqueado.")

    
    # Actualizar last_login
    user.last_login = datetime.now(timezone.utc)

    token = create_access_token(
        {
            "sub": str(user.id),
            "rol": user.rol.value,
        }
    )

    cohorte = AuthService.build_login_cohort(
        db,
        user,
    )

    registrar(
        db,
        "LOGIN",
        usuario_id=user.id,
        ip=_get_ip(request),
    )

    db.commit()

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        rol=user.rol,
        user_id=user.id,
        cohorte=cohorte,
    )
    
@router.post("/activate")
def activate_account(payload: ActivateAccountRequest, db: Session = Depends(get_db)):
    """
    Activación de tutor: verifica token temporal y establece contraseña.
    El token es un JWT de activación de 24h generado al crear el tutor.
    """
    from backend.utils.security import decode_token
    from jose import JWTError
    try:
        data = decode_token(payload.token)
        user_id = data.get("sub")
        purpose = data.get("purpose")
        if purpose != "activation":
            raise HTTPException(status_code=400, detail="Token inválido.")
    except JWTError:
        raise HTTPException(status_code=400, detail="Token inválido o expirado.")

    user = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not user or user.estado != EstadoUsuario.PENDIENTE:
        raise HTTPException(status_code=400, detail="Usuario no encontrado o ya activado.")

    user.password_hash = hash_password(payload.password)
    user.estado = EstadoUsuario.ACTIVO
    registrar(db, "ACTIVATE_TUTOR", usuario_id=user.id)
    db.commit()
    return {"message": "Cuenta activada exitosamente."}


@router.get("/me", response_model=UsuarioResponse)
def me(current_user: Usuario = Depends(get_current_user)):
    return current_user
