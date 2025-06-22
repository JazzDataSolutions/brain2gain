# 🛠️ Development Setup Guide

Complete setup guide for Brain2Gain development environment.

## 📋 Prerequisites

### Required Software
- **Docker & Docker Compose** (latest)
- **Node.js 20+** (LTS recommended)
- **Python 3.10+** (for backend development)
- **Git** (latest)

### Optional Tools
- **uv** (ultra-fast Python package manager) - recommended
- **VS Code** with recommended extensions
- **Postman/Insomnia** for API testing

## 🚀 Quick Setup

### 1. Clone Repository
```bash
git clone https://github.com/JazzDataSolutions/brain2gain.git
cd brain2gain
```

### 2. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit with your settings
nano .env
```

**Key Environment Variables:**
```env
# Database
DATABASE_URL=postgresql://brain2gain_owner:ClaveDura!2025@localhost:5433/brain2gain_prod

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=RedisPass2025

# Security
SECRET_KEY=your-super-secret-key-here

# Development
DEBUG=true
ENVIRONMENT=development
```

### 3. Start Development Environment
```bash
# Using Make (recommended)
make dev

# Or using Docker Compose directly
docker-compose -f docker-compose.dev.yml up --build
```

### 4. Access Applications
- 🌐 **Frontend**: http://localhost:5173
- 🔧 **API Documentation**: http://localhost:8000/docs
- 📊 **Admin Panel**: http://localhost:5173/admin
- 🗄️ **Database Admin**: http://localhost:8080
- 🚦 **Traefik Dashboard**: http://localhost:8090

## 🔧 Development Modes

### Full Development (Default)
```bash
make dev
```
Includes: Frontend + Backend + Database + Redis + Adminer

### Backend Only
```bash
make backend
cd backend
uv sync
source .venv/bin/activate
fastapi run --reload
```

### Frontend Only
```bash
make frontend
cd frontend
npm install
npm run dev
```

### Production-like Environment
```bash
docker-compose -f docker-compose.yml up --build
```

## 📦 Package Management

### Backend (Python)
We use **uv** for ultra-fast dependency management:

```bash
cd backend

# Install dependencies (creates venv automatically)
uv sync

# Activate virtual environment
source .venv/bin/activate

# Add new dependency
uv add fastapi[all]

# Add development dependency
uv add --group dev pytest

# Update dependencies
uv lock --upgrade
```

### Frontend (Node.js)
```bash
cd frontend

# Install dependencies
npm install

# Add new dependency
npm install package-name

# Add development dependency
npm install -D package-name

# Update dependencies
npm update
```

## 🗄️ Database Management

### Migrations
```bash
cd backend

# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Downgrade migration
alembic downgrade -1

# Check migration status
alembic current
```

### Database Reset
```bash
# Stop containers
docker-compose down

# Remove volumes (data will be lost!)
docker-compose down -v

# Restart with fresh database
make dev
```

## 🧪 Testing

### All Tests
```bash
make test
```

### Backend Tests
```bash
cd backend
pytest
pytest tests/api/routes/test_users.py -v
pytest --cov=app tests/
```

### Frontend Tests
```bash
cd frontend

# Unit tests
npm run test

# E2E tests
npm run test:e2e

# Test specific component
npm run test -- ProductCard.test.tsx
```

### API Testing
```bash
# Using curl
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Using httpie
http GET localhost:8000/api/v1/users/me \
  Authorization:"Bearer YOUR_TOKEN"
```

## 🔍 Code Quality

### Linting & Formatting
```bash
# All projects
make lint
make format

# Backend only
cd backend
ruff check .
ruff format .
mypy app/

# Frontend only
cd frontend
npm run lint
npm run format
npx tsc --noEmit
```

### Pre-commit Hooks
```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run manually
pre-commit run --all-files
```

## 🐛 Debugging

### Backend Debugging
```bash
# Enable debug logs
export LOG_LEVEL=DEBUG

# Run with debugger
cd backend
python -m debugpy --listen 5678 --wait-for-client -m uvicorn app.main:app --reload
```

### Frontend Debugging
- Use browser DevTools
- React DevTools extension
- Redux DevTools for state management

### Database Debugging
```bash
# Connect to database directly
docker exec -it brain2gain-postgres psql -U brain2gain_owner -d brain2gain_prod

# View logs
docker logs brain2gain-postgres
docker logs brain2gain-backend
```

## 🔧 Common Issues

### Port Conflicts
```bash
# Check what's using port
lsof -i :5173
lsof -i :8000

# Kill process
kill -9 PID
```

### Permission Issues
```bash
# Fix Docker permissions
sudo chown -R $USER:$USER .

# Fix node_modules permissions
cd frontend
rm -rf node_modules
npm install
```

### Database Connection Issues
```bash
# Check database status
docker ps | grep postgres

# Restart database
docker-compose restart postgres

# Check connection
docker exec -it brain2gain-postgres pg_isready
```

### Cache Issues
```bash
# Clear Redis cache
docker exec -it brain2gain-redis redis-cli FLUSHALL

# Clear npm cache
npm cache clean --force

# Clear Docker cache
docker system prune -af
```

## 🚀 Performance Tips

### Development Speed
1. Use **uv** instead of pip for Python dependencies
2. Enable **Docker BuildKit** for faster builds
3. Use **incremental TypeScript compilation**
4. Enable **React Fast Refresh**

### Resource Usage
```bash
# Limit Docker memory usage
docker-compose -f docker-compose.dev.yml up --scale postgres=1

# Monitor resource usage
docker stats

# Clean up unused containers
docker system prune
```

## 📱 Mobile Development

### Testing Mobile UI
```bash
cd frontend

# Test on different viewports
npm run dev -- --host 0.0.0.0

# Access from mobile device
# Use your computer's IP: http://192.168.1.xxx:5173
```

### PWA Development
```bash
# Build PWA
npm run build

# Test PWA features
npm run preview
```

## 🌐 API Client Generation

### Generate TypeScript Client
```bash
cd frontend
npm run generate-client

# Manually generate
npx openapi-ts --input http://localhost:8000/openapi.json --output src/client
```

### Update API Schema
```bash
# After backend changes
cd backend
fastapi run --reload

# In another terminal
cd frontend
npm run generate-client
```

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)

## 🆘 Getting Help

1. **Check the logs** first
2. **Search existing issues** on GitHub
3. **Create detailed issue** with reproduction steps
4. **Join our discussions** for general questions

```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs backend
docker-compose logs frontend
```