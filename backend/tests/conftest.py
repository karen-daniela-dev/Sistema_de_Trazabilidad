"""
Configuración de pytest y fixtures compartidas.
Usa una BD de test separada — nunca la de desarrollo.
"""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Forzar entorno de test ANTES de importar la app
os.environ["ENVIRONMENT"] = "testing"
os.environ["DATABASE_URL"] = "postgresql://empleabilidad_user:secret@localhost:5432/empleabilidad_test"
os.environ["SECRET_KEY"] = "test-secret-key-only-for-tests"
os.environ["DEBUG"] = "false"

from backend.database import Base, get_db
from backend.main import app
from backend.models.enums import RolEnum, EstadoUsuario, EstadoCohorte
from backend.models.usuario import Usuario
from backend.models.cohorte import Cohorte
from backend.models.aprendiz_perfil import AprendizPerfil
from backend.utils.security import hash_password, create_access_token
from backend.services.cohort_engine import fecha_fin_desde_inicio
from datetime import date, timedelta
import uuid

TEST_DB_URL = os.environ["DATABASE_URL"]

engine_test = create_engine(TEST_DB_URL, pool_pre_ping=True)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    """Crea todas las tablas al inicio de la sesión de test."""
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)


@pytest.fixture
def db():
    """Sesión de BD que hace rollback al finalizar cada test."""
    connection = engine_test.connect()
    transaction = connection.begin()
    session = TestSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db):
    """TestClient con sesión de BD inyectada."""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


# ── Factories ─────────────────────────────────────────────────────────────────

def make_usuario(db, rol=RolEnum.APRENDIZ, estado=EstadoUsuario.ACTIVO, email=None) -> Usuario:
    u = Usuario(
        email=email or f"test_{uuid.uuid4().hex[:8]}@test.com",
        password_hash=hash_password("Test@1234"),
        rol=rol,
        estado=estado,
        activo=True,
    )
    db.add(u)
    db.flush()
    return u


def make_cohorte(db, estado=EstadoCohorte.ACTIVA, permitir_extension=False) -> Cohorte:
    inicio = date.today() - timedelta(days=30)
    c = Cohorte(
        nombre=f"Cohorte Test {uuid.uuid4().hex[:4]}",
        fecha_inicio=inicio,
        fecha_fin=fecha_fin_desde_inicio(inicio),
        estado=estado,
        meta_contratacion=10,
        permitir_extension=permitir_extension,
    )
    db.add(c)
    db.flush()
    return c


def make_perfil(db, usuario, cohorte, tutor) -> AprendizPerfil:
    p = AprendizPerfil(
        usuario_id=usuario.id,
        cohorte_id=cohorte.id,
        tutor_id=tutor.id,
        ciudad="Bogotá",
    )
    db.add(p)
    db.flush()
    return p


def auth_headers(usuario: Usuario) -> dict:
    token = create_access_token({"sub": str(usuario.id), "rol": usuario.rol.value})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def coordinador(db):
    return make_usuario(db, rol=RolEnum.COORDINADOR)


@pytest.fixture
def tutor(db):
    return make_usuario(db, rol=RolEnum.TUTOR)


@pytest.fixture
def aprendiz(db):
    return make_usuario(db, rol=RolEnum.APRENDIZ)


@pytest.fixture
def cohorte_activa(db):
    return make_cohorte(db, estado=EstadoCohorte.ACTIVA)


@pytest.fixture
def setup_aprendiz_completo(db, aprendiz, tutor, cohorte_activa):
    """Aprendiz con perfil completo listo para registrar aplicaciones."""
    perfil = make_perfil(db, aprendiz, cohorte_activa, tutor)
    return aprendiz, tutor, cohorte_activa, perfil
