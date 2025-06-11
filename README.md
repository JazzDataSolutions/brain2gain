# 🧠💪 Brain2Gain - Plataforma de Suplementos Deportivos

[![CI/CD Pipeline](https://github.com/JazzDataSolutions/brain2gain/actions/workflows/ci.yml/badge.svg)](https://github.com/JazzDataSolutions/brain2gain/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/release/python-3100/)
[![Node Version](https://img.shields.io/badge/node-20+-green.svg)](https://nodejs.org/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

**Brain2Gain** es una plataforma moderna de e-commerce especializada en suplementos deportivos, diseñada para ofrecer una experiencia de compra excepcional y herramientas de gestión empresarial integradas.

![Diagrama de Entidad-Relación](docs/er_diagram.png)

## 🎯 Visión del Proyecto

**Brain2Gain** combina una **tienda online moderna** con un **sistema ERP completo**, ofreciendo tanto experiencia de compra optimizada para clientes como herramientas de gestión empresarial integradas.

### 🛒 Experiencia Cliente (B2C)
- **Tienda optimizada**: Catálogo intuitivo con búsqueda avanzada
- **Checkout express**: Compra rápida con/sin registro 
- **Mobile-first**: PWA responsive para móviles
- **Personalización**: Recomendaciones basadas en historial

### 🏢 Gestión Empresarial (B2B)
- **Dashboard ejecutivo**: Métricas en tiempo real
- **Control inventario**: Multi-almacén con alertas automáticas
- **CRM integrado**: Gestión completa de clientes y leads
- **Finanzas**: Reportes automáticos y control de flujo

## 🏗️ Arquitectura Técnica

### Stack Tecnológico Actual
```yaml
Backend:
  Framework: FastAPI 0.114+
  Database: PostgreSQL 17
  ORM: SQLModel + Alembic
  Authentication: JWT + OAuth2
  Cache: Redis 7.2+ (implementado)
  Rate Limiting: SlowAPI + avanzado
  Package Manager: uv (ultra-fast)

Frontend:
  Framework: React 18 + TypeScript
  Build: Vite 5
  UI: Chakra UI + Tailwind CSS
  Routing: TanStack Router
  State: TanStack Query + Zustand
  Testing: Playwright + Vitest
  Linting: Biome (sustituto de ESLint/Prettier)

Deployment:
  Containerization: Docker + Docker Compose
  Environment Separation: Store/Admin modes
  CI/CD: GitHub Actions
  Monitoring: Health checks + Sentry
  Documentation: Sphinx + auto-generated
  Code Quality: Ruff, MyPy, Biome
```

### Arquitectura Evolutiva
El proyecto está diseñado para evolucionar de **monolito modular** hacia **microservicios** siguiendo el plan detallado en [`ARCHITECTURE_PROPOSAL.md`](./ARCHITECTURE_PROPOSAL.md).

## 🚀 Inicio Rápido

### Prerrequisitos
- Docker y Docker Compose
- Node.js 20+ (para desarrollo frontend)
- Python 3.10+ (para desarrollo backend)

### Instalación

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/JazzDataSolutions/brain2gain.git
   cd brain2gain
   ```

2. **Configurar variables de entorno**
   ```bash
   cp .env.example .env
   # Editar .env con tus configuraciones
   ```

3. **Levantar el entorno de desarrollo**
   ```bash
   make dev
   ```

4. **Acceder a las aplicaciones**
   - 🌐 **Frontend**: http://localhost:5173
   - 🔧 **API Docs**: http://localhost:8000/docs
   - 📊 **Admin Panel**: http://localhost:5173/admin

### Comandos Disponibles

```bash
# Desarrollo
make dev              # Levantar entorno completo
make frontend         # Solo frontend
make backend          # Solo backend

# Testing
make test             # Ejecutar todas las pruebas
make test-backend     # Pruebas del backend (pytest)
make test-frontend    # Pruebas del frontend (vitest + playwright)

# Calidad de código
make lint             # Linting completo (ruff + biome)
make format           # Formatear código

# Backend específico
cd backend
uv sync               # Instalar dependencias ultra-rápido
fastapi run --reload  # Servidor desarrollo
pytest                # Ejecutar tests
alembic upgrade head  # Aplicar migraciones

# Frontend específico  
cd frontend
npm run dev           # Servidor desarrollo
npm run test:e2e      # Tests end-to-end
npm run generate-client  # Generar cliente API
```

## 📋 Estado del Desarrollo

### ✅ Completado
- **Infraestructura base**: FastAPI + React + PostgreSQL + Docker
- **Autenticación**: Sistema JWT con roles y refresh tokens
- **Base de datos**: Modelos optimizados con índices de rendimiento
- **Cache**: Redis implementado con estrategias avanzadas
- **Rate Limiting**: Middleware avanzado de limitación
- **Testing**: Configuración completa Pytest y Playwright
- **CI/CD**: Pipeline con análisis de código y seguridad
- **Documentación**: Auto-generada y actualizada

### 🔧 En Desarrollo Activo
- **API endpoints**: Se están corrigiendo y estandarizando rutas
- **Sistema de carrito**: Implementación completa en progreso
- **Frontend modular**: Separación tienda/admin en proceso
- **Métricas**: Analytics básico y reportes

### 🎯 Próximas Funcionalidades
- **Checkout completo**: Proceso de pago y confirmación
- **Gestión de pedidos**: Estados y seguimiento
- **Integración de pagos**: Pasarelas de pago locales
- **Sistema de notificaciones**: Email y push notifications
- **Reportes avanzados**: Analytics y métricas de negocio

## 📊 Mejoras Planificadas

### Fase 1: Optimizaciones Inmediatas ⚡ (EN PROGRESO)
Ver detalles completos en [`IMMEDIATE_IMPROVEMENTS.md`](./IMMEDIATE_IMPROVEMENTS.md):
- ✅ **Cache con Redis** (-70% queries a BD) - IMPLEMENTADO
- ✅ **Rate limiting avanzado** - IMPLEMENTADO  
- 🔧 **Separación de interfaces** (Tienda vs Admin) - EN DESARROLLO
- 🔧 **Analytics básico** (métricas de conversión) - EN DESARROLLO

### Fase 2: Separación de Dominios (Semanas 3-8)
- 🏪 **Subdominio tienda**: `tienda.brain2gain.com`
- 🏢 **Subdominio ERP**: `erp.brain2gain.com`
- 🚪 **API Gateway**: Kong para gestión de tráfico
- 📦 **Microservicios**: Auth, Products, Orders, Inventory

### Fase 3: Funcionalidades Avanzadas (Mes 3+)
- 🤖 **IA para recomendaciones** de productos
- 📱 **App móvil** React Native
- 🌍 **Internacionalización** y multi-moneda
- 🔄 **Integraciones** con marketplaces

## 📂 Estructura del Proyecto

```
brain2gain/
├── backend/                    # API FastAPI
│   ├── app/
│   │   ├── api/               # Endpoints REST
│   │   ├── core/              # Configuración y seguridad
│   │   ├── models.py          # Modelos SQLModel
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Lógica de negocio
│   │   ├── repositories/      # Acceso a datos
│   │   └── tests/            # Pruebas automatizadas
│   ├── alembic/              # Migraciones de BD
│   └── Dockerfile
│
├── frontend/                   # React + TypeScript
│   ├── src/
│   │   ├── components/        # Componentes reutilizables
│   │   ├── routes/           # Páginas y routing
│   │   ├── stores/           # Estado global
│   │   ├── client/           # Cliente API generado
│   │   └── tests/            # Pruebas E2E
│   └── Dockerfile
│
├── docs/                      # Documentación Sphinx
├── scripts/                   # Scripts de automatización
├── docker-compose.yml         # Orquestación contenedores
├── Makefile                  # Comandos automatizados
└── README.md                 # Este archivo
```

## 🧪 Testing y Calidad

### Cobertura de Pruebas
- **Backend**: Pytest con cobertura >85%
- **Frontend**: Vitest + Playwright para E2E
- **API**: Pruebas de integración automáticas
- **Security**: Análisis estático y dependencias

### Estándares de Código
- **Python**: Ruff (linting + formatting), MyPy (tipos)
- **TypeScript**: Biome (linting + formatting), TypeScript strict
- **Git**: Conventional Commits + pre-commit hooks
- **Docker**: Multi-stage builds optimizados
- **Package Managers**: uv (Python), npm (JavaScript)

## 🚢 Despliegue

### Entornos
- **Desarrollo**: Docker Compose local
- **Staging**: Deploy automático en develop
- **Producción**: Deploy manual con aprobación

### Infraestructura Recomendada
```yaml
Mínimo (MVP):
  - VPS: 4 vCPU, 8GB RAM, 100GB SSD
  - Database: PostgreSQL gestionado
  - CDN: CloudFlare para assets
  - Monitoring: Sentry + logs básicos

Producción (Scale):
  - Kubernetes: 3 nodes mínimo
  - Database: Cluster PostgreSQL + Redis
  - Load Balancer: NGINX/Traefik
  - Observability: Prometheus + Grafana
```

Ver detalles completos en [`deployment.md`](./deployment.md).

## 👨‍💻 Desarrollo

### Configuración del Entorno

1. **Backend** (usando uv para gestión ultra-rápida)
   ```bash
   cd backend
   uv sync  # Instala automáticamente venv + dependencias
   source .venv/bin/activate
   fastapi run --reload
   ```

2. **Frontend**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

### Contribución
1. Fork del repositorio
2. Crear rama feature: `git checkout -b feature/nueva-funcionalidad`
3. Commit cambios: `git commit -m 'feat: agregar nueva funcionalidad'`
4. Push a la rama: `git push origin feature/nueva-funcionalidad`
5. Crear Pull Request

## 📈 Métricas y KPIs

### Objetivos Técnicos
- **Performance**: Time to First Byte < 200ms
- **Disponibilidad**: Uptime > 99.9%
- **Errores**: Error rate < 0.1%
- **Escalabilidad**: 1000+ pedidos/día

### Objetivos de Negocio
- **Conversión**: Rate > 3%
- **AOV**: Ticket promedio +25%
- **Retención**: Customer LTV +40%
- **Operaciones**: Eficiencia +50%

## 📚 Documentación

- **API**: Documentación automática en `/docs`
- **Arquitectura**: [`ARCHITECTURE_PROPOSAL.md`](./ARCHITECTURE_PROPOSAL.md)
- **Mejoras**: [`IMMEDIATE_IMPROVEMENTS.md`](./IMMEDIATE_IMPROVEMENTS.md)
- **Desarrollo**: [`CLAUDE.md`](./CLAUDE.md) - Guía para IA asistentes
- **Despliegue**: [`deployment.md`](./deployment.md)
- **Testing**: [`TESTING_GUIDE.md`](./TESTING_GUIDE.md)
- **Releases**: [`release-notes.md`](./release-notes.md)

### Generar Documentación
```bash
cd docs
pip install -r requirements.txt
make html
```

## 🔐 Seguridad

- **Autenticación**: JWT con refresh tokens
- **Autorización**: RBAC granular
- **Encriptación**: Passwords con bcrypt
- **Validación**: Sanitización de inputs
- **CORS**: Configuración restrictiva
- **Headers**: Security headers completos

## 📄 Licencia

Este proyecto está licenciado bajo la Licencia MIT. Ver [`LICENSE`](./LICENSE) para más detalles.

## 🤝 Soporte

- **Issues**: [GitHub Issues](https://github.com/JazzDataSolutions/brain2gain/issues)
- **Discusiones**: [GitHub Discussions](https://github.com/JazzDataSolutions/brain2gain/discussions)
- **Email**: soporte@brain2gain.com

---

**Desarrollado con ❤️ para la comunidad fitness**

*"Transformamos la tecnología en resultados reales para tu negocio"*