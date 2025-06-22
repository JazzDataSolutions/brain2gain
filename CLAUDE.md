# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Brain2Gain is an e-commerce platform for sports supplements built with FastAPI (backend) and React/TypeScript (frontend). The project uses PostgreSQL + Redis, Docker for containerization, and follows a modular monolith architecture designed to evolve toward microservices.

## Development Commands

### Quick Start
```bash
make dev          # Start full development environment with Docker
make test         # Run all tests (backend + frontend)
make lint         # Run linting for all codebases
make build        # Build frontend for production
```

### Backend (`/backend/`)
```bash
cd backend
uv sync                    # Install Python dependencies (ultra-fast)
source .venv/bin/activate  # Activate virtual environment
fastapi run --reload       # Run development server on port 8000
./scripts/test.sh          # Run tests with coverage
./scripts/lint.sh          # Run linting (mypy + ruff)
pytest tests/api/routes/test_login.py::test_login  # Run specific test
alembic upgrade head       # Apply database migrations
```

### Frontend (`/frontend/`)
```bash
cd frontend
npm run dev           # Start development server on port 5173
npm run build         # Build for production (includes TypeScript compilation)
npm run test          # Run unit tests with Vitest
npm run test:coverage # Run tests with coverage report
npm run test:e2e      # Run Playwright E2E tests
npm run lint          # Run Biome linting and formatting
npm run generate-client  # Generate API client from OpenAPI spec
```

## Architecture

### Current Architecture (Transitioning to Microservices - Phase 2)
The project is evolving from a modular monolith to microservices architecture:

**Microservices (Active Development)**:
- **Auth Service** (`/services/auth-service/`) - Centralized authentication with JWT
- **Product Service** (`/services/product-service/`) - Catalog and pricing management  
- **Order Service** (`/services/order-service/`) - Order processing (in development)
- **Inventory Service** (`/services/inventory-service/`) - Stock management (in development)

### Backend Structure (Legacy Monolith)
- **FastAPI** app with async support, using `uv` for dependency management
- **SQLModel** ORM with PostgreSQL 17
- **JWT authentication** with role-based access control (User, Admin, Manager, Seller, Accountant)
- **Redis** for caching and session management
- **Alembic** for database migrations
- **Repository pattern** in `/repositories/` for data access
- **Service layer** in `/services/` for business logic
- **Ruff** for linting and formatting (replaces black + isort + flake8)

### Frontend Structure
- **React 18** with TypeScript and Vite
- **TanStack Router** for type-safe routing with route-based code splitting
- **Chakra UI + Tailwind CSS** for styling
- **TanStack Query** for server state management
- **Zustand** for client state (cart store)
- **OpenAPI client** auto-generated from backend schema using `@hey-api/openapi-ts`
- **Biome** for linting and formatting (replaces ESLint + Prettier)
- **Vitest** for unit testing, **Playwright** for E2E testing

### Key Database Models
- `User` (UUID-based with role relationships)
- `Product` (with SKU, pricing, stock tracking)
- `Cart/CartItem` (shopping cart functionality)
- `SalesOrder/SalesItem` (order management)
- `Transaction` (financial tracking)

## Testing

- **Backend**: Pytest with fixtures in `/tests/conftest.py`, enhanced with coverage reports
- **Frontend**: Vitest for unit tests, Playwright for E2E with accessibility testing
- **Test databases**: Automatic cleanup between tests using pytest-postgresql
- **Microservices**: Independent test suites per service
- Run specific test files: `pytest tests/api/routes/test_users.py`
- Coverage reports: `./scripts/test.sh` generates HTML coverage reports

## Environment Setup

1. Copy `.env.example` to `.env` and configure database/Redis URLs
2. Use Docker Compose for development: `docker-compose -f docker-compose.dev.yml up`
3. Access points:
   - Frontend: http://localhost:5173
   - Legacy API docs: http://localhost:8000/docs
   - Auth Service: http://localhost:8001/docs
   - Product Service: http://localhost:8002/docs
   - Admin panel: http://localhost:5173/admin

## Code Standards

- **Backend**: Follow existing FastAPI patterns, use async/await, implement proper error handling
- **Frontend**: Use TypeScript strictly, follow existing component patterns in `/components/`
- **Database**: All migrations through Alembic, use UUID for primary keys
- **API**: Follow OpenAPI spec generation, maintain backward compatibility
- **Microservices**: Each service should be independently deployable and testable
- **Linting**: Use `ruff` for Python, `biome` for TypeScript/JavaScript
- **Testing**: Maintain >85% coverage for both backend and frontend

## Working with Microservices

### Running Individual Services
```bash
# Auth Service (port 8001)
cd services/auth-service
uvicorn app.main:app --reload --port 8001

# Product Service (port 8002)  
cd services/product-service
uvicorn app.main:app --reload --port 8002

# Order Service (port 8003) - in development
cd services/order-service
uvicorn app.main:app --reload --port 8003
```

### Service Communication
- Services communicate via HTTP APIs
- Auth Service provides JWT validation for other services
- Each service has its own database schema/namespace
- Use service discovery patterns for inter-service communication

## Common Issues

- **CORS errors**: Check `core/config.py` CORS settings for legacy backend, individual service configs for microservices
- **Database migrations**: Run `alembic upgrade head` after model changes
- **Frontend build errors**: Regenerate API client with `npm run generate-client`
- **Docker issues**: Use `docker-compose down -v` to reset volumes
- **Microservice communication**: Ensure all required services are running and accessible
- **Port conflicts**: Check that services are running on their designated ports (8001, 8002, etc.)