"""
Tests unitarios — Seguridad: contraseñas y JWT.
"""
import pytest
import time
from datetime import timedelta

from backend.utils.security import (
    hash_password, verify_password, validate_password_strength,
    create_access_token, decode_token,
)
from jose import JWTError


class TestPasswordValidation:
    def test_contrasena_valida(self):
        validate_password_strength("Test@1234")  # no debe lanzar

    def test_sin_mayuscula_falla(self):
        with pytest.raises(ValueError):
            validate_password_strength("test@1234")

    def test_sin_numero_falla(self):
        with pytest.raises(ValueError):
            validate_password_strength("Test@abcd")

    def test_sin_especial_falla(self):
        with pytest.raises(ValueError):
            validate_password_strength("Test12345")

    def test_muy_corta_falla(self):
        with pytest.raises(ValueError):
            validate_password_strength("T@1a")

    def test_solo_letras_falla(self):
        with pytest.raises(ValueError):
            validate_password_strength("TestAbcd")


class TestPasswordHashing:
    def test_hash_distinto_del_original(self):
        hashed = hash_password("Test@1234")
        assert hashed != "Test@1234"

    def test_verificacion_correcta(self):
        hashed = hash_password("Test@1234")
        assert verify_password("Test@1234", hashed) is True

    def test_verificacion_incorrecta(self):
        hashed = hash_password("Test@1234")
        assert verify_password("Wrong@1234", hashed) is False

    def test_mismo_password_distinto_hash(self):
        """bcrypt genera salt único cada vez."""
        h1 = hash_password("Test@1234")
        h2 = hash_password("Test@1234")
        assert h1 != h2

    def test_password_debil_no_se_hashea(self):
        with pytest.raises(ValueError):
            hash_password("debil")


class TestJWT:
    def test_crear_y_decodificar_token(self):
        token = create_access_token({"sub": "user-123", "rol": "APRENDIZ"})
        data = decode_token(token)
        assert data["sub"] == "user-123"
        assert data["rol"] == "APRENDIZ"

    def test_token_expirado_lanza_error(self):
        token = create_access_token({"sub": "user-123"}, expires_delta=timedelta(seconds=-1))
        with pytest.raises(JWTError):
            decode_token(token)

    def test_token_invalido_lanza_error(self):
        with pytest.raises(JWTError):
            decode_token("esto.no.es.un.token")

    def test_token_modificado_lanza_error(self):
        token = create_access_token({"sub": "user-123"})
        token_mod = token[:-5] + "XXXXX"
        with pytest.raises(JWTError):
            decode_token(token_mod)

    def test_payload_contiene_exp(self):
        token = create_access_token({"sub": "user-123"})
        data = decode_token(token)
        assert "exp" in data
