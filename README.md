# Brain2Gain - E-commerce de Suplementos 💪

[![CI/CD Pipeline](https://github.com/JazzDataSolutions/brain2gain/actions/workflows/ci.yml/badge.svg)](https://github.com/JazzDataSolutions/brain2gain/actions/workflows/ci.yml)
[![Security Scan](https://github.com/JazzDataSolutions/brain2gain/actions/workflows/security.yml/badge.svg)](https://github.com/JazzDataSolutions/brain2gain/actions/workflows/security.yml)
[![Backend Coverage](https://codecov.io/gh/JazzDataSolutions/brain2gain/branch/main/graph/badge.svg?flag=backend)](https://codecov.io/gh/JazzDataSolutions/brain2gain)
[![Frontend Coverage](https://codecov.io/gh/JazzDataSolutions/brain2gain/branch/main/graph/badge.svg?flag=frontend)](https://codecov.io/gh/JazzDataSolutions/brain2gain)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=JazzDataSolutions_brain2gain&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=JazzDataSolutions_brain2gain)
[![Reliability Rating](https://sonarcloud.io/api/project_badges/measure?project=JazzDataSolutions_brain2gain&metric=reliability_rating)](https://sonarcloud.io/summary/new_code?id=JazzDataSolutions_brain2gain)
[![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=JazzDataSolutions_brain2gain&metric=security_rating)](https://sonarcloud.io/summary/new_code?id=JazzDataSolutions_brain2gain)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=JazzDataSolutions_brain2gain&metric=sqale_rating)](https://sonarcloud.io/summary/new_code?id=JazzDataSolutions_brain2gain)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/release/python-3100/)
[![Node Version](https://img.shields.io/badge/node-20+-green.svg)](https://nodejs.org/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

**Brain2Gain** es una plataforma moderna de comercio electrónico especializada en suplementos deportivos, diseñada para ofrecer una experiencia completa tanto para clientes como administradores.

## Arquitectura

![Diagrama de Entidad-Relación](docs/er_diagram.png)
        
## 🎯 Objetivos del Proyecto

### Funcionalidades Core
- 🛒 **E-commerce completo** - Catálogo, carrito, checkout con/sin registro
- 📊 **Dashboard administrativo** - Gestión de ventas, métricas y pedidos
- 📦 **Gestión de inventario** - Control de stock en tiempo real
- 👥 **Sistema de usuarios** - Roles (admin, empleado), perfiles personalizados
- 🎁 **Ofertas especiales** - Promociones y compras recurrentes
- 🌐 **Compra como invitado** - Checkout sin necesidad de registro

### Características Técnicas
- ⚡ **Alto rendimiento** con FastAPI y React moderno
- 🔒 **Seguridad** con JWT y roles de usuario
- 📱 **Responsive design** con Chakra UI
- 🐋 **Containerización** completa con Docker
- 🧪 **Testing** automatizado (Pytest + Playwright)
- 📈 **Monitoreo** con Sentry

El proyecto utiliza una arquitectura moderna basada en la plantilla "Full Stack FastAPI + React" con las mejores prácticas de desarrollo.

## 🚀 Plan de Desarrollo

### 📋 Estado Actual
- ✅ **Infraestructura base** - FastAPI + React + PostgreSQL + Docker
- ✅ **Autenticación** - JWT con roles de usuario
- ✅ **Testing** - Configuración inicial de Pytest y Playwright
- ⚠️ **API de productos** - Requiere corrección y estandarización
- ❌ **Sistema de carrito** - Pendiente implementación
- ❌ **Checkout** - Pendiente implementación

### 🎯 Fase 1: Core E-commerce (Semanas 1-3)

#### Backend
- [ ] **Arreglar API de productos**
  - Resolver nombres en español vs inglés
  - Estandarizar modelos Product vs Producto
  - Incluir rutas en main router
- [ ] **Sistema de carrito**
  - Implementar `CartService` y `CartRepository`
  - Endpoints para agregar/quitar/actualizar productos
  - Persistencia de carrito para usuarios registrados
- [ ] **Mejorar modelos**
  - Validaciones de negocio para productos
  - Relaciones optimizadas entre entidades

#### Frontend
- [ ] **Páginas de productos dinámicas**
  - Catálogo con datos de API real
  - Página de detalle de producto
  - Filtros y búsqueda básica
- [ ] **Sistema de carrito**
  - Estado global con Zustand/Context
  - Componentes de carrito (mini-cart, cart page)
  - Persistencia en localStorage

### 🎯 Fase 2: Procesamiento de Pedidos (Semanas 4-6)

#### Backend
- [ ] **Servicios de pedidos**
  - `OrderService` para gestión de pedidos
  - Estados de pedido (pending, confirmed, shipped, delivered)
  - Validación de stock disponible
- [ ] **Gestión de inventario**
  - `InventoryService` para control de stock
  - Actualizaciones automáticas en pedidos
  - Alertas de stock bajo

#### Frontend
- [ ] **Flujo de checkout**
  - Proceso paso a paso (cart → info → payment → confirmation)
  - Formularios de dirección y pago
  - Página de confirmación de pedido
- [ ] **Gestión de pedidos**
  - Historial de pedidos para usuarios
  - Estado de seguimiento
  - Panel de administración básico

### 🎯 Fase 3: Funcionalidades Avanzadas (Semanas 7-10)

#### Backend
- [ ] **Integración de pagos**
  - API de procesamiento de pagos
  - Webhook para confirmaciones
  - Gestión de transacciones

#### Frontend
- [ ] **Panel de administración**
  - Gestión de productos (CRUD)
  - Dashboard de ventas y métricas
  - Gestión de pedidos
- [ ] **Mejoras UX**
  - PWA capabilities
  - Optimización de imágenes
  - SEO para productos

## Technology Stack and Features

- ⚡ [**FastAPI**](https://fastapi.tiangolo.com) for the Python backend API.
    - 🧰 [SQLModel](https://sqlmodel.tiangolo.com) for the Python SQL database interactions (ORM).
    - 🔍 [Pydantic](https://docs.pydantic.dev), used by FastAPI, for the data validation and settings management.
    - 💾 [PostgreSQL](https://www.postgresql.org) as the SQL database.
- 🚀 [React](https://react.dev) for the frontend.
    - 💃 Using TypeScript, hooks, Vite, and other parts of a modern frontend stack.
    - 🎨 [Chakra UI](https://chakra-ui.com) for the frontend components.
    - 🔀 [TanStack Router](https://tanstack.com/router) for type-safe routing.
    - 🔄 [TanStack Query](https://tanstack.com/query) for server state management.
    - 🤖 An automatically generated frontend client.
    - 🧪 [Playwright](https://playwright.dev) for End-to-End testing.
    - 🦇 Dark mode support.
- 🐋 [Docker Compose](https://www.docker.com) for development and production.
- 🔒 Secure password hashing by default.
- 🔑 JWT (JSON Web Token) authentication.
- 📫 Email based password recovery.
- ✅ Tests with [Pytest](https://pytest.org).
- 📞 [Traefik](https://traefik.io) as a reverse proxy / load balancer.
- 🚢 Deployment instructions using Docker Compose, including how to set up a frontend Traefik proxy to handle automatic HTTPS certificates.
- 🏭 CI (continuous integration) and CD (continuous deployment) based on GitHub Actions.

## 🔄 CI/CD Pipeline Status

Our comprehensive CI/CD pipeline ensures code quality, security, and reliable deployments:

### ✅ Automated Testing
- **Backend Tests**: Unit tests, integration tests, and API tests with coverage reporting
- **Frontend Tests**: Component tests, E2E tests with Playwright
- **Security Scanning**: Vulnerability detection in dependencies and Docker images
- **Code Quality**: Linting, formatting, and type checking

### 🚀 Deployment Pipeline
- **Staging**: Automatic deployment on `develop` branch
- **Production**: Deployment on release tags with manual approval
- **Rollback**: Quick rollback capability for production issues

### 📊 Quality Metrics
- **Test Coverage**: Maintained above 80% for critical components
- **Code Quality**: SonarCloud integration for maintainability
- **Security**: Daily security scans and dependency updates
- **Performance**: Automated performance monitoring

### 🛡️ Security & Compliance
- **Dependabot**: Automated dependency updates
- **SAST**: Static Application Security Testing
- **Container Scanning**: Docker image vulnerability assessment
- **License Compliance**: Automated license checking

## Quickstart

1. Create or copy the `.env` file at the project root and fill in the required variables (see `deployment.md` for details).
2. Start the development environment:
   ```bash
   make dev
   ```
3. Open your browser:
   - Backend API docs: http://localhost:8000/docs
   - Frontend: http://localhost:5173

### Configure

You can then update configs in the `.env` files to customize your configurations.

Before deploying it, make sure you change at least the values for:

- `SECRET_KEY`
- `FIRST_SUPERUSER_PASSWORD`
- `POSTGRES_PASSWORD`

You can (and should) pass these as environment variables from secrets.

Read the [deployment.md](./deployment.md) docs for more details.

### Generate Secret Keys

Some environment variables in the `.env` file have a default value of `changethis`.

You have to change them with a secret key, to generate secret keys you can run the following command:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the content and use that as password / secret key. And run that again to generate another secure key.

## Backend Development

Backend docs: [backend/README.md](./backend/README.md).

## Frontend Development

Frontend docs: [frontend/README.md](./frontend/README.md).

## Deployment

Deployment docs: [deployment.md](./deployment.md).

## Development

General development docs: [development.md](./development.md).

This includes using Docker Compose, custom local domains, `.env` configurations, etc.

## Release Notes

Check the file [release-notes.md](./release-notes.md).

## Documentation

La documentación completa (arquitectura, plan de trabajo, endpoints, pruebas, despliegue) se genera con Sphinx.

Para compilarla localmente:
```bash
cd docs
pip install -r requirements.txt
make html
```
Los archivos HTML resultantes se ubican en `docs/_build/html`.

## License

The Full Stack FastAPI Template is licensed under the terms of the MIT license.