SHELL := /bin/bash

.PHONY: dev test lint build ci production stop clean logs help

# === ENVIRONMENT COMMANDS ===
dev:
	@echo "🚀 Starting development environment with hot reload..."
	docker compose -f docker-compose.dev.yml up --build -d
	@echo "✅ Development environment started!"
	@echo "   Frontend: http://localhost:5173"
	@echo "   Backend API: http://localhost:8000"
	@echo "   Admin: http://localhost:8080"
	@echo "   Mailcatcher: http://localhost:1080"

production:
	@echo "🏭 Starting production environment..."
	docker compose up --build -d
	@echo "✅ Production environment started!"
	@echo "   Application: http://localhost"
	@echo "   API: http://localhost:8000"

ci:
	@echo "🔬 Running CI tests..."
	docker compose -f docker-compose.ci.yml up --build --abort-on-container-exit
	@echo "✅ CI tests completed!"

# === DEVELOPMENT TOOLS ===
dev-tools:
	@echo "🛠️ Starting development tools..."
	docker compose -f docker-compose.dev.yml --profile tools up -d

dev-testing:
	@echo "🧪 Starting testing environment..."
	docker compose -f docker-compose.dev.yml --profile testing up -d

# === STOP & CLEANUP ===
stop:
	@echo "🛑 Stopping all environments..."
	docker compose down
	docker compose -f docker-compose.dev.yml down
	docker compose -f docker-compose.ci.yml down

clean:
	@echo "🧹 Cleaning up containers and volumes..."
	docker compose down -v --remove-orphans
	docker compose -f docker-compose.dev.yml down -v --remove-orphans
	docker compose -f docker-compose.ci.yml down -v --remove-orphans
	docker system prune -f
	@echo "✅ Cleanup completed!"

# === TESTING COMMANDS ===
test:
	@echo "🧪 Running local tests..."
	cd backend && uv run pytest
	cd frontend && npm run test

test-backend:
	@echo "🧪 Running backend tests..."
	cd backend && uv run pytest --cov=app --cov-report=html --cov-report=term-missing

test-frontend:
	@echo "🧪 Running frontend tests..."
	cd frontend && npm run test:coverage

test-e2e:
	@echo "🎭 Running E2E tests..."
	docker compose -f docker-compose.dev.yml --profile testing up -d playwright

test-integration:
	@echo "🔗 Running integration tests..."
	cd backend && uv run pytest tests/integration/ -v

test-all:
	@echo "🚀 Running all tests via CI..."
	make ci

# === LINTING COMMANDS ===
lint:
	@echo "🔍 Running linting..."
	cd backend && uv run ruff check app && uv run ruff format app --check
	cd frontend && npm run lint

lint-fix:
	@echo "🔧 Fixing linting issues..."
	cd backend && uv run ruff check app --fix && uv run ruff format app
	cd frontend && npm run lint:fix

type-check:
	@echo "📝 Running type checking..."
	cd backend && uv run mypy app
	cd frontend && npm run build  # TypeScript compilation serves as type check

# === BUILD COMMANDS ===
build:
	@echo "🏗️ Building frontend..."
	cd frontend && npm run build

build-backend:
	@echo "🏗️ Building backend Docker image..."
	docker compose build backend

build-frontend:
	@echo "🏗️ Building frontend Docker image..."
	docker compose build frontend

build-all:
	@echo "🏗️ Building all Docker images..."
	docker compose build

# === UTILITY COMMANDS ===
logs:
	@echo "📋 Showing logs (Ctrl+C to exit)..."
	docker compose logs -f

logs-dev:
	@echo "📋 Showing development logs (Ctrl+C to exit)..."
	docker compose -f docker-compose.dev.yml logs -f

logs-backend:
	docker compose logs -f backend

logs-frontend:
	docker compose logs -f frontend

status:
	@echo "📊 Environment status:"
	docker compose ps

shell-backend:
	@echo "🐚 Opening backend shell..."
	docker compose exec backend bash

shell-db:
	@echo "🗄️ Opening database shell..."
	docker compose exec postgres psql -U brain2gain_user -d brain2gain

# === BACKEND DEVELOPMENT ===
run-backend:
	@echo "🏃 Running backend locally..."
	cd backend && uv run fastapi dev app/main.py --port 8000

shell-backend-local:
	@echo "🐚 Starting backend Python shell..."
	cd backend && uv run python

generate-migration:
	@echo "📝 Generating new database migration..."
	cd backend && uv run alembic revision --autogenerate -m "$(name)"

upgrade-db:
	@echo "⬆️ Upgrading database to latest migration..."
	cd backend && uv run alembic upgrade head

# === DATABASE COMMANDS ===
db-reset:
	@echo "🗄️ Resetting database..."
	docker compose exec postgres psql -U brain2gain_user -d brain2gain -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
	make upgrade-db

db-backup:
	@echo "💾 Creating database backup..."
	mkdir -p ./database/backups
	docker compose exec postgres pg_dump -U brain2gain_user brain2gain > ./database/backups/backup_$(shell date +%Y%m%d_%H%M%S).sql

db-restore:
	@echo "📥 Restoring database from backup: $(file)"
	docker compose exec -T postgres psql -U brain2gain_user -d brain2gain < $(file)

# === FRONTEND DEVELOPMENT ===
run-frontend:
	@echo "🏃 Running frontend locally..."
	cd frontend && npm run dev

generate-client:
	@echo "🔄 Generating API client from OpenAPI spec..."
	cd frontend && npm run generate-client

# === QUICK ACCESS ===
open-app:
	@echo "🌐 Opening application in browser..."
	open http://localhost:5173

open-api:
	@echo "📚 Opening API documentation..."
	open http://localhost:8000/docs

open-admin:
	@echo "🛠️ Opening database admin..."
	open http://localhost:8080

# === HELP COMMAND ===
help:
	@echo "📖 Brain2Gain Development Commands:"
	@echo ""
	@echo "🚀 Environment Management:"
	@echo "  dev                 - Start development environment with hot reload"
	@echo "  production          - Start production environment"
	@echo "  ci                  - Run CI tests"
	@echo "  stop                - Stop all environments"
	@echo "  clean               - Clean containers, volumes, and images"
	@echo ""
	@echo "🧪 Testing:"
	@echo "  test                - Run local tests"
	@echo "  test-backend        - Run backend tests with coverage"
	@echo "  test-frontend       - Run frontend tests with coverage"
	@echo "  test-e2e            - Run E2E tests"
	@echo "  test-all            - Run all tests via CI"
	@echo ""
	@echo "🔍 Code Quality:"
	@echo "  lint                - Run linting"
	@echo "  lint-fix            - Fix linting issues"
	@echo "  type-check          - Run type checking"
	@echo ""
	@echo "🏗️ Building:"
	@echo "  build               - Build frontend"
	@echo "  build-all           - Build all Docker images"
	@echo ""
	@echo "🗄️ Database:"
	@echo "  db-reset            - Reset database schema"
	@echo "  upgrade-db          - Run database migrations"
	@echo "  generate-migration  - Generate new migration (name=<description>)"
	@echo ""
	@echo "🌐 Quick Access:"
	@echo "  open-app            - Open application (http://localhost:5173)"
	@echo "  open-api            - Open API docs (http://localhost:8000/docs)"
	@echo "  open-admin          - Open DB admin (http://localhost:8080)"
	@echo ""
	@echo "📋 Utilities:"
	@echo "  logs                - Show all logs"
	@echo "  status              - Show container status"
	@echo "  shell-backend       - Open backend shell"
	@echo "  shell-db            - Open database shell"
