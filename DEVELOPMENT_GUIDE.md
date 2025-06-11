# 🛠️ Brain2Gain - Development Guide

Esta guía consolida toda la información de desarrollo para Brain2Gain.

## 🚀 Quick Start

### Requisitos Previos
- Docker & Docker Compose
- Node.js 20+
- Python 3.10+ (opcional para desarrollo local)

### Inicio Rápido

```bash
# Clonar repositorio
git clone <repository-url>
cd brain2gain

# Iniciar desarrollo completo
make dev

# O manualmente:
docker-compose -f docker-compose.dev.yml up --build
```

### URLs de Desarrollo
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Adminer (DB)**: http://localhost:8080
- **Traefik Dashboard**: http://localhost:8090

## 🏗️ Estructura del Proyecto

```
brain2gain/
├── backend/           # FastAPI application
│   ├── app/          # Application code
│   ├── scripts/      # Backend scripts
│   └── tests/        # Backend tests
├── frontend/         # React application
│   ├── src/          # Source code
│   └── tests/        # Frontend tests
├── scripts/          # Project-wide scripts
├── docs/             # Documentation
└── *.yml             # Docker Compose configurations
```

## 🛠️ Scripts Consolidados

### Testing
```bash
# Todos los tests
./scripts/test-consolidated.sh

# Solo backend
./scripts/test-consolidated.sh -t backend

# Solo frontend  
./scripts/test-consolidated.sh -t frontend

# E2E tests
./scripts/test-consolidated.sh -t e2e

# Tests de ambientes
./scripts/test-consolidated.sh -t env
```

### Building
```bash
# Build completo
./scripts/build-consolidated.sh

# Build solo tienda
./scripts/build-consolidated.sh -m store

# Build solo admin
./scripts/build-consolidated.sh -m admin

# Build y push
./scripts/build-consolidated.sh -p
```

## 🌍 Separación de Ambientes

### Modo Store (Solo Tienda)
```bash
cp .env.store .env
docker-compose -f docker-compose.store.yml up -d
```
- **Puerto**: 3000 (frontend), 8000 (API)
- **Funcionalidad**: Solo e-commerce público

### Modo Admin (Solo ERP)
```bash
cp .env.admin .env
docker-compose -f docker-compose.admin.yml up -d
```
- **Puerto**: 3001 (frontend), 8001 (API), 8080 (DB)
- **Funcionalidad**: Solo panel administrativo

Ver [README-environments.md](./README-environments.md) para detalles completos.

## 🧪 Testing Strategy

### Backend Tests
```bash
cd backend
source .venv/bin/activate
pytest tests/ -v
```

### Frontend Tests
```bash
cd frontend
npm run test        # Unit tests
npm run test:e2e    # E2E tests
```

### Coverage
```bash
# Backend coverage
cd backend && coverage run -m pytest && coverage report

# Frontend coverage
cd frontend && npm run test:coverage
```

## 📦 Dependency Management

### Backend (Python)
```bash
cd backend
uv add <package>           # Add dependency
uv sync                    # Install dependencies
uv lock                    # Update lock file
```

### Frontend (Node.js)
```bash
cd frontend
npm install <package>      # Add dependency
npm ci                     # Install from lock
npm audit fix              # Fix vulnerabilities
```

## 🔧 Development Workflow

### Feature Development
1. **Branch**: `git checkout -b feature/nueva-funcionalidad`
2. **Develop**: Hacer cambios siguiendo las convenciones
3. **Test**: `./scripts/test-consolidated.sh`
4. **Lint**: `make lint`
5. **Commit**: Siguiendo Conventional Commits
6. **PR**: Crear Pull Request

### Database Migrations
```bash
# Crear migración
cd backend
alembic revision --autogenerate -m "Descripción del cambio"

# Aplicar migraciones
alembic upgrade head

# Rollback
alembic downgrade -1
```

### API Client Generation
```bash
cd frontend
npm run generate-client
```

## 🔒 Security & Quality

### Pre-commit Hooks
```bash
# Instalar hooks
pre-commit install

# Ejecutar manualmente
pre-commit run --all-files
```

### Code Quality
```bash
# Backend
cd backend
ruff check .           # Linting
ruff format .          # Formatting
mypy app/              # Type checking

# Frontend
cd frontend
npm run lint           # Biome linting
npm run format         # Biome formatting
npm run typecheck      # TypeScript checking
```

## 🐛 Debugging

### Backend Debug
```bash
# Logs en tiempo real
docker-compose logs -f backend

# Debug con breakpoints
docker-compose -f docker-compose.dev.yml up
# Conectar debugger al puerto 5678
```

### Frontend Debug
```bash
# DevTools habilitado automáticamente
# Chrome DevTools + React DevTools
# Vite HMR activo
```

### Database Debug
```bash
# Acceder a Adminer
open http://localhost:8080

# CLI directo
docker-compose exec postgres psql -U brain2gain_owner -d brain2gain_prod
```

## 📊 Performance Monitoring

### Health Checks
```bash
curl http://localhost:8000/health    # Backend health
curl http://localhost:5173          # Frontend health
```

### Metrics
- **Backend**: `/metrics` endpoint (Prometheus format)
- **Frontend**: Web Vitals automáticos
- **Database**: Queries monitoring en logs

## 🔄 CI/CD Pipeline

### GitHub Actions
- **Push**: Tests automáticos
- **PR**: Tests + Linting + Security scan
- **Merge to main**: Deploy automático

### Local CI Simulation
```bash
./scripts/test-consolidated.sh -e ci
```

## 📚 Documentation

### API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Code Documentation
```bash
# Backend
cd backend && sphinx-build -b html docs/ docs/_build/

# Frontend
cd frontend && npm run docs
```

## 🚨 Troubleshooting

### Problemas Comunes

#### Containers no inician
```bash
docker-compose down -v
docker-compose up --build
```

#### Base de datos corrupta
```bash
docker volume rm brain2gain_postgres_data
docker-compose up -d postgres
```

#### Node modules corruptos
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

#### Caché de Python
```bash
find . -type d -name __pycache__ -exec rm -r {} +
```

### Logs Útiles
```bash
# Todos los servicios
docker-compose logs

# Servicio específico
docker-compose logs backend

# En tiempo real
docker-compose logs -f
```

## 📞 Support & Resources

- **Issues**: GitHub Issues
- **Docs**: `/docs` folder
- **API Reference**: http://localhost:8000/docs
- **Architecture**: [ARCHITECTURE_PROPOSAL.md](./ARCHITECTURE_PROPOSAL.md)
- **Testing**: [TESTING_GUIDE.md](./TESTING_GUIDE.md)

---

> 💡 **Tip**: Usa `make help` para ver todos los comandos disponibles del Makefile.