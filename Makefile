SHELL := /bin/bash

.PHONY: help dev test prod tools clean setup logs status

# ═══════════════════════════════════════════════════════════════════
# 🚀 Brain2Gain - Simplified Development Commands
# ═══════════════════════════════════════════════════════════════════

help: ## Show this help message
	@echo "Brain2Gain Development Commands"
	@echo "================================"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Environment Management

setup: ## Setup development environment
	@echo "🔧 Setting up development environment..."
	@./scripts/env-manager.sh setup development
	@echo "✅ Development environment configured!"

dev: ## Start development environment with hot reload
	@echo "🚀 Starting development environment..."
	@./scripts/env-manager.sh start development
	@echo "✅ Development environment started!"
	@echo "   Frontend: http://localhost:5173"
	@echo "   Backend API: http://localhost:8000"
	@echo "   Admin: http://localhost:8080"
	@echo "   Mailcatcher: http://localhost:1080"

test-env: ## Start testing environment
	@echo "🧪 Starting testing environment..."
	@./scripts/env-manager.sh start testing
	@echo "✅ Testing environment started!"

prod: ## Start production environment
	@echo "🏭 Starting production environment..."
	@./scripts/env-manager.sh setup production
	@./scripts/env-manager.sh start production

##@ Testing Commands

test-setup: ## Setup testing environment
	@./scripts/test-manager.sh setup

test: ## Run all tests
	@./scripts/test-manager.sh all

test-unit: ## Run unit tests only
	@./scripts/test-manager.sh unit

test-integration: ## Run integration tests
	@./scripts/test-manager.sh integration

test-e2e: ## Run end-to-end tests
	@./scripts/test-manager.sh e2e

test-security: ## Run security tests
	@./scripts/test-manager.sh security

test-performance: ## Run performance tests
	@./scripts/test-manager.sh performance

test-coverage: ## Generate coverage reports
	@./scripts/test-manager.sh coverage

test-backend: ## Run backend tests only
	@./scripts/test-manager.sh all --backend-only

test-frontend: ## Run frontend tests only
	@./scripts/test-manager.sh all --frontend-only

test-fast: ## Run fast tests (skip slow integration and e2e)
	@./scripts/test-manager.sh all --fast

##@ Development Tools

tools: ## Start development tools (Adminer, Mailcatcher)
	@echo "🛠️ Starting development tools..."
	@docker compose -f docker/compose.development.yml --profile tools up -d
	@echo "✅ Tools started: Adminer (8080), Mailcatcher (1080)"

logs: ## Show logs for development environment
	@./scripts/env-manager.sh logs development

status: ## Show environment status
	@./scripts/env-manager.sh status development

##@ Cleanup Commands

stop: ## Stop current environment
	@echo "🛑 Stopping environment..."
	@./scripts/env-manager.sh stop development 2>/dev/null || true
	@./scripts/env-manager.sh stop testing 2>/dev/null || true
	@./scripts/env-manager.sh stop production 2>/dev/null || true

clean: ## Clean all environments and volumes
	@echo "🧹 Cleaning all environments..."
	@./scripts/env-manager.sh clean development 2>/dev/null || true
	@./scripts/env-manager.sh clean testing 2>/dev/null || true
	@./scripts/test-manager.sh clean

clean-test: ## Clean only testing environment
	@./scripts/test-manager.sh clean

##@ Quick Commands

quick-start: setup dev ## Setup and start development environment
	@echo "🎉 Quick start completed!"

quick-test: test-setup test-fast ## Setup and run fast tests
	@echo "🎉 Quick test completed!"

full-test: test-setup test ## Setup and run all tests
	@echo "🎉 Full test suite completed!"

##@ Advanced Commands

backend-shell: ## Access backend container shell
	@docker exec -it brain2gain-backend-dev /bin/bash

frontend-shell: ## Access frontend container shell
	@docker exec -it brain2gain-frontend-dev /bin/bash

db-shell: ## Access database shell
	@docker exec -it brain2gain-postgres-dev psql -U $(POSTGRES_USER) -d $(POSTGRES_DB)

reset: stop clean setup dev ## Reset entire development environment
	@echo "🔄 Environment reset completed!"

##@ Information

info: ## Show environment information
	@echo "Brain2Gain Development Environment Info"
	@echo "======================================="
	@echo ""
	@echo "📁 Project Structure:"
	@echo "   config/          - Environment configurations"
	@echo "   docker/          - Docker compose files"
	@echo "   scripts/         - Management scripts"
	@echo "   backend/         - FastAPI backend"
	@echo "   frontend/        - React frontend"
	@echo ""
	@echo "🔧 Available Environments:"
	@echo "   development      - Hot reload, debugging tools"
	@echo "   testing          - Isolated testing environment"
	@echo "   production       - Optimized for production"
	@echo ""
	@echo "🧪 Testing Categories:"
	@echo "   unit             - Fast unit tests"
	@echo "   integration      - Database and API tests"
	@echo "   e2e              - End-to-end browser tests"
	@echo "   security         - Security validation"
	@echo "   performance      - Load and performance tests"

# Default target
.DEFAULT_GOAL := help