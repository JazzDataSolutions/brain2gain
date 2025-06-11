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
uv sync                    # Install Python dependencies
source .venv/bin/activate  # Activate virtual environment
fastapi run --reload       # Run development server on port 8000
pytest                     # Run backend tests
pytest tests/api/routes/test_login.py::test_login  # Run specific test
alembic upgrade head       # Apply database migrations
```

### Frontend (`/frontend/`)
```bash
npm run dev           # Start development server on port 5173
npm run build         # Build for production
npm run test          # Run unit tests with Vitest
npm run test:e2e      # Run Playwright E2E tests
npm run lint          # Run Biome linting
npm run generate-client  # Generate API client from OpenAPI spec
```

## Architecture

### Backend Structure
- **FastAPI** app with async support
- **SQLModel** ORM with PostgreSQL 17
- **JWT authentication** with role-based access control (User, Admin, Manager, Seller, Accountant)
- **Redis** for caching and session management
- **Alembic** for database migrations
- **Repository pattern** in `/repositories/` for data access
- **Service layer** in `/services/` for business logic

### Frontend Structure
- **React 18** with TypeScript and Vite
- **TanStack Router** for type-safe routing
- **Chakra UI + Tailwind CSS** for styling
- **TanStack Query** for server state management
- **Zustand** for client state (cart store)
- **OpenAPI client** auto-generated from backend schema

### Key Database Models
- `User` (UUID-based with role relationships)
- `Product` (with SKU, pricing, stock tracking)
- `Cart/CartItem` (shopping cart functionality)
- `SalesOrder/SalesItem` (order management)
- `Transaction` (financial tracking)

## Testing

- **Backend**: Pytest with fixtures in `/tests/conftest.py`
- **Frontend**: Vitest for unit tests, Playwright for E2E
- **Test databases**: Automatic cleanup between tests
- Run specific test files: `pytest tests/api/routes/test_users.py`

## Environment Setup

1. Copy `.env.example` to `.env` and configure database/Redis URLs
2. Use Docker Compose for development: `docker-compose -f docker-compose.dev.yml up`
3. Access points:
   - Frontend: http://localhost:5173
   - API docs: http://localhost:8000/docs
   - Admin panel: http://localhost:5173/admin

## Code Standards

- **Backend**: Follow existing FastAPI patterns, use async/await, implement proper error handling
- **Frontend**: Use TypeScript strictly, follow existing component patterns in `/components/`
- **Database**: All migrations through Alembic, use UUID for primary keys
- **API**: Follow OpenAPI spec generation, maintain backward compatibility

## Common Issues

- **CORS errors**: Check `core/config.py` CORS settings
- **Database migrations**: Run `alembic upgrade head` after model changes
- **Frontend build errors**: Regenerate API client with `npm run generate-client`
- **Docker issues**: Use `docker-compose down -v` to reset volumes