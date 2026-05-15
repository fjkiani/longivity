.PHONY: dev backend frontend install test migrate reset help

# ── Development ───────────────────────────────────────────────────────────────

dev: ## Start backend + frontend (requires postgres running)
	@echo "Starting Longivity..."
	@make -j2 backend frontend

backend: ## Start FastAPI backend on :8000
	cd $(CURDIR) && uvicorn longivity.app:app --reload --host 0.0.0.0 --port 8000

frontend: ## Start Next.js frontend on :3000
	cd $(CURDIR)/web && npm run dev

# ── Docker ────────────────────────────────────────────────────────────────────

docker-up: ## Start full stack with Docker Compose
	docker compose up --build

docker-down: ## Stop Docker Compose
	docker compose down

docker-reset: ## Reset Docker Compose (drops volumes)
	docker compose down -v

# ── Setup ─────────────────────────────────────────────────────────────────────

install: ## Install all dependencies
	pip install -e ".[dev]" sqlalchemy[asyncio] asyncpg alembic python-jose[cryptography] passlib[bcrypt] pdfplumber python-multipart aiofiles psycopg2-binary
	cd web && npm install

# ── Database ──────────────────────────────────────────────────────────────────

migrate: ## Run Alembic migrations
	alembic upgrade head

db-reset: ## Drop and recreate database
	psql -U longivity -c "DROP DATABASE IF EXISTS longivity; CREATE DATABASE longivity;"
	make migrate

# ── Testing ───────────────────────────────────────────────────────────────────

test: ## Run all tests
	pytest tests/ -v

test-api: ## Quick API smoke test (requires running backend)
	@echo "Testing auth..."
	curl -s -X POST http://localhost:8000/api/v1/auth/register \
		-H "Content-Type: application/json" \
		-d '{"email":"test@clinic.com","password":"testpass123","full_name":"Dr. Test","clinic_name":"Test Clinic"}' | python3 -m json.tool
	@echo "\nTesting healthz..."
	curl -s http://localhost:8000/api/v1/longevity/healthz | python3 -m json.tool

# ── Help ──────────────────────────────────────────────────────────────────────

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
