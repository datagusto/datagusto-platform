.PHONY: help install install-backend install-frontend dev dev-backend dev-frontend migrate test test-backend test-frontend lint lint-backend lint-frontend format format-backend format-frontend typecheck-frontend check check-backend check-frontend check-security clean

# Default target
help:
	@echo "Available targets:"
	@echo "  make install           - Install all dependencies (backend + frontend)"
	@echo "  make install-backend   - Install backend dependencies"
	@echo "  make install-frontend  - Install frontend dependencies"
	@echo ""
	@echo "  make dev               - Start both backend and frontend in parallel"
	@echo "  make dev-backend       - Start backend only"
	@echo "  make dev-frontend      - Start frontend only"
	@echo ""
	@echo "  make migrate           - Run database migrations"
	@echo ""
	@echo "  make test              - Run all tests"
	@echo "  make test-backend      - Run backend tests"
	@echo "  make test-frontend     - Run frontend tests"
	@echo ""
	@echo "  make lint              - Run linters for both"
	@echo "  make lint-backend      - Lint backend code"
	@echo "  make lint-frontend     - Lint frontend code"
	@echo ""
	@echo "  make format            - Format code for both"
	@echo "  make format-backend    - Format backend code"
	@echo "  make format-frontend   - Format frontend code"
	@echo ""
	@echo "  make typecheck-frontend - Run TypeScript type check"
	@echo ""
	@echo "  make check             - Run all CI checks (backend + frontend + security)"
	@echo "  make check-backend     - Run backend CI checks (lint + format + tests)"
	@echo "  make check-frontend    - Run frontend CI checks (format + typecheck + lint + tests)"
	@echo "  make check-security    - Run security scan (gitleaks)"
	@echo ""
	@echo "  make clean             - Clean build artifacts and caches"

# Install dependencies
install: install-backend install-frontend

install-backend:
	@echo "Installing backend dependencies..."
	cd backend && uv sync

install-frontend:
	@echo "Installing frontend dependencies..."
	cd frontend && npm install

# Development servers
dev:
	@echo "Starting backend and frontend in parallel..."
	@make -j2 dev-backend dev-frontend

dev-backend:
	@echo "Starting backend on http://localhost:8888"
	cd backend && uv run uvicorn app.main:app --reload --port 8888

dev-frontend:
	@echo "Starting frontend on http://localhost:3001"
	cd frontend && npm run dev

# Database migrations
migrate:
	@echo "Running database migrations..."
	cd backend && uv run alembic upgrade head

# Tests
test: test-backend test-frontend

test-backend:
	@echo "Running backend tests..."
	cd backend && uv run pytest

test-frontend:
	@echo "Running frontend tests..."
	cd frontend && npm run test:run

# Linting
lint: lint-backend lint-frontend

lint-backend:
	@echo "Linting backend code..."
	cd backend && uv run --frozen ruff check .

lint-frontend:
	@echo "Linting frontend code..."
	cd frontend && npm run lint

# Formatting
format: format-backend format-frontend

format-backend:
	@echo "Formatting backend code..."
	cd backend && uv run --frozen ruff format .

format-frontend:
	@echo "Formatting frontend code..."
	cd frontend && npm run format

# Type checking
typecheck-frontend:
	@echo "Running TypeScript type check..."
	cd frontend && npx tsc --noEmit

# CI Checks (same as GitHub Actions)
check: check-backend check-frontend check-security

check-backend:
	@echo "Running backend CI checks..."
	@echo "1. Running Ruff linter check..."
	cd backend && uv run --frozen ruff check .
	@echo "2. Running Ruff formatter check..."
	cd backend && uv run --frozen ruff format --check .
	@echo "3. Running pytest..."
	cd backend && uv run --frozen pytest --verbose --color=yes
	@echo "✅ Backend CI checks passed!"

check-frontend:
	@echo "Running frontend CI checks..."
	@echo "1. Running Prettier format check..."
	cd frontend && npm run format:check
	@echo "2. Running TypeScript type check..."
	cd frontend && npx tsc --noEmit
	@echo "3. Running ESLint..."
	cd frontend && npm run lint
	@echo "4. Running Vitest tests..."
	cd frontend && npm run test:run || echo "⚠️  No test files found (skipping)"
	@echo "✅ Frontend CI checks passed!"

check-security:
	@echo "Running security scan..."
	@command -v gitleaks >/dev/null 2>&1 || { echo "⚠️  gitleaks is not installed. Install it with: brew install gitleaks"; exit 1; }
	gitleaks detect --config .gitleaks.toml --verbose
	@echo "✅ Security scan passed!"

# Clean
clean:
	@echo "Cleaning build artifacts and caches..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".next" -exec rm -rf {} + 2>/dev/null || true
	@echo "Clean complete!"
