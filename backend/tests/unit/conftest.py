"""
Conftest aislado para tests unitarios.
Parchea el engine de SQLAlchemy para evitar conexión real a PostgreSQL.
"""
import os
os.environ["ENVIRONMENT"] = "testing"
os.environ["SECRET_KEY"] = "test-secret-key-only-for-tests"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["DATABASE_URL_TEST"] = "sqlite:///:memory:"

# Parchear ANTES de que cualquier módulo del backend se importe
import sys

# Remover módulos cacheados del backend si ya fueron importados
for mod in list(sys.modules.keys()):
    if mod.startswith("backend"):
        del sys.modules[mod]
