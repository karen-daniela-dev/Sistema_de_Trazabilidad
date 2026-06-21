"""
Gestión de la conexión y sesiones SQLAlchemy.
El engine se crea en módulo level, pero con pool_pre_ping y parámetros
adaptados al dialecto (PostgreSQL en prod, SQLite en test).
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from backend.config import settings


class Base(DeclarativeBase):
    pass


def build_engine(url: str):
    is_sqlite = url.startswith("sqlite")
    kwargs: dict = {"pool_pre_ping": True, "echo": settings.DEBUG}
    if not is_sqlite:
        kwargs.update({"pool_size": 10, "max_overflow": 20, "pool_timeout": 30})
    return create_engine(url, **kwargs)


engine = build_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency FastAPI — inyecta sesión y garantiza cierre."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_all_tables():
    """Crea todas las tablas (solo para dev/test)."""
    import backend.models  # noqa: F401
    Base.metadata.create_all(bind=engine)


def drop_all_tables():
    Base.metadata.drop_all(bind=engine)
