.PHONY: dev test test-unit test-integration test-security coverage lint format clean db-up db-down

# ── Desarrollo ────────────────────────────────────────────────────────────────

dev-backend:
	uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

dev-frontend:
	streamlit run frontend/app.py --server.port 8501

dev:
	# Iniciar backend y frontend en paralelo
	make dev-backend & make dev-frontend

# ── Docker ────────────────────────────────────────────────────────────────────

db-up:
	docker compose up db -d

db-test-up:
	docker compose --profile test up db_test -d

db-down:
	docker compose down

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down -v

# ── Tests ─────────────────────────────────────────────────────────────────────

test:
	pytest backend/tests/ -v

test-unit:
	pytest backend/tests/unit/ -v -m unit

test-integration:
	pytest backend/tests/integration/ -v -m integration

test-security:
	pytest backend/tests/security/ -v -m security

coverage:
	pytest backend/tests/ --cov=backend --cov-report=html:coverage_report
	@echo "Reporte en coverage_report/index.html"

# ── Calidad de código ─────────────────────────────────────────────────────────

lint:
	ruff check backend/ frontend/

format:
	black backend/ frontend/

# ── Base de datos ─────────────────────────────────────────────────────────────

migrate:
	alembic upgrade head

migrate-create:
	alembic revision --autogenerate -m "$(msg)"

migrate-rollback:
	alembic downgrade -1

# ── Utilidades ────────────────────────────────────────────────────────────────

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	find . -name "*.pyc" -delete
	rm -rf coverage_report .coverage

seed:
	python -m scripts.seed_dev_data

setup-dev: db-up
	cp .env.example .env
	pip install -r requirements.txt
	@echo "✅ Entorno listo. Edita .env con tus valores y ejecuta 'make dev-backend'"
