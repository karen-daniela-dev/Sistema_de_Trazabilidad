"""
Configuración central del sistema.
Lee variables desde .env — nunca hardcodear secretos.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    APP_NAME: str = "Sistema de Empleabilidad"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql://empleabilidad_user:secret@localhost:5432/empleabilidad_db"
    DATABASE_URL_TEST: str = "postgresql://empleabilidad_user:secret@localhost:5432/empleabilidad_test"

    # JWT
    SECRET_KEY: str = "changeme-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # CORS
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:8501",
        "http://127.0.0.1:8501",
    ]

    # Rate limiting
    RATE_LIMIT_LOGIN: str = "10/minute"
    RATE_LIMIT_API: str = "100/minute"

    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@empleabilidad.com"

    # Frontend
    API_BASE_URL: str = "http://localhost:8000"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_testing(self) -> bool:
        return self.ENVIRONMENT == "testing"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
