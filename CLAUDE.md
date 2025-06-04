# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment Setup
```bash
make dev                    # Start development environment (Docker Compose)
```

### Testing
```bash
# Backend tests
cd backend && pytest                    # Run backend unit tests
cd backend && bash scripts/test.sh      # Run with coverage report

# Frontend tests
cd frontend && npm test                 # Run E2E tests with Playwright

# All tests
make test                              # Run both backend and frontend tests
```

### Code Quality
```bash
# Backend linting and formatting
cd backend && bash scripts/lint.sh     # Run mypy, ruff check, ruff format
cd backend && ruff check app           # Just linting
cd backend && ruff format app          # Just formatting

# Frontend linting
cd frontend && npm run lint            # Run Biome (replaces ESLint/Prettier)

# All linting
make lint                             # Run both backend and frontend linting
```

### Build
```bash
cd frontend && npm run build          # Build frontend for production
make build                           # Same as above
```

### API Client Generation
```bash
cd frontend && npm run generate-client # Generate TypeScript client from OpenAPI spec
```

## Architecture Overview

### Backend (FastAPI + PostgreSQL)
- **Framework**: FastAPI with SQLModel/SQLAlchemy ORM
- **Database**: PostgreSQL with Alembic migrations
- **Auth**: JWT tokens with role-based access (admin, manager, seller, accountant)
- **Package Manager**: UV (modern Python dependency manager)
- **Structure**: Clean architecture with routes → services → repositories → models

Key directories:
- `backend/app/api/routes/` - API endpoints
- `backend/app/services/` - Business logic
- `backend/app/repositories/` - Data access layer
- `backend/app/models.py` - SQLModel database models
- `backend/app/schemas/` - Pydantic schemas for API validation

### Frontend (React + TypeScript)
- **Framework**: React 18 with TypeScript and Vite
- **UI Library**: Chakra UI
- **Routing**: TanStack Router (type-safe)
- **State Management**: TanStack Query + Zustand (cart store)
- **Auto-generated API Client**: Generated from backend OpenAPI spec

Key directories:
- `frontend/src/components/` - React components organized by feature
- `frontend/src/routes/` - TanStack Router route definitions
- `frontend/src/client/` - Auto-generated API client (don't edit manually)
- `frontend/src/stores/` - Zustand state stores

## Development Environment

### Services (Docker Compose)
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Frontend**: http://localhost:5173
- **Database Admin**: http://localhost:8080 (Adminer)
- **PostgreSQL**: localhost:5432
- **MailCatcher**: http://localhost:1080 (development email testing)

### Configuration
- Environment variables in `.env` file at project root
- Backend config in `backend/app/core/config.py`
- Frontend config in Vite setup

## Current Implementation Status

### ✅ Working
- Basic FastAPI backend with PostgreSQL
- React frontend with Chakra UI
- JWT authentication with role system
- Docker development environment
- Testing setup (Pytest + Playwright)
- Basic product API endpoints

### ⚠️ Known Issues
- Product API has naming inconsistencies (Spanish vs English)
- Cart backend service needs implementation
- Some models use inconsistent naming (Product vs Producto)

### 🚧 In Progress
- Complete cart system implementation
- Product catalog integration
- Order management system

## Important Notes

### Database Migrations
```bash
cd backend
alembic revision --autogenerate -m "description"  # Create migration
alembic upgrade head                               # Apply migrations
```

### API Client Regeneration
When backend API changes, regenerate the frontend client:
```bash
# Start backend first
make dev
# Then regenerate client
cd frontend && npm run generate-client
```

### Code Style Guidelines
- Backend uses Ruff for linting/formatting (replaces Black + isort + flake8)
- Frontend uses Biome for linting/formatting (replaces ESLint + Prettier)
- Type safety is enforced: mypy for Python, TypeScript for frontend
- Follow existing patterns in each layer (routes → services → repositories)

### Business Domain
Brain2Gain is an e-commerce platform for sports supplements with:
- Product catalog with real-time inventory
- Shopping cart (guest and registered users)
- Multi-role user system
- Order processing and tracking
- Administrative dashboard for sales management