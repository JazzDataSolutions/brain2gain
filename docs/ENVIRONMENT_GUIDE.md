# 🔧 Environment Management Guide

## 📋 Estructura Simplificada

### 🗂️ Nueva Organización de Archivos

```
Brain2Gain/
├── config/                     # 🔧 Configuraciones centralizadas
│   ├── .env.base               # Configuración base compartida
│   ├── .env.development        # Desarrollo con hot reload
│   ├── .env.testing            # Testing aislado
│   └── .env.production         # Producción optimizada
├── docker/                     # 🐳 Compose files organizados
│   ├── compose.base.yml        # Servicios base (DB, Redis)
│   ├── compose.development.yml # Entorno desarrollo
│   ├── compose.testing.yml     # Entorno testing
│   └── compose.production.yml  # Entorno producción
├── scripts/                    # 🚀 Scripts unificados
│   ├── env-manager.sh          # Gestor de entornos
│   └── test-manager.sh         # Gestor de tests
└── Makefile                    # 📋 Comandos simplificados
```

### Preparar archivos de entorno

Copie el archivo `.env.example` en la carpeta `config/` para cada entorno:

```bash
cp .env.example config/.env.development
cp .env.example config/.env.testing
cp .env.example config/.env.production
```

## 🚀 Comandos Principales

### Gestión de Entornos

```bash
# Configurar entorno de desarrollo
make setup

# Iniciar desarrollo con hot reload
make dev

# Configurar y ejecutar tests
make test-setup
make test

# Ver estado de contenedores
make status

# Ver logs en tiempo real
make logs
```

### Testing Simplificado

```bash
# Tests completos
make test

# Tests rápidos (sin E2E)
make test-fast

# Tests específicos
make test-unit           # Solo unit tests
make test-integration    # Solo integration tests
make test-e2e           # Solo end-to-end tests
make test-security      # Solo security tests

# Tests por componente
make test-backend       # Solo backend
make test-frontend      # Solo frontend

# Cobertura de código
make test-coverage
```

### Limpieza y Mantenimiento

```bash
# Parar entornos
make stop

# Limpiar todo
make clean

# Reset completo
make reset
```

## 🔧 Gestión Avanzada con Scripts

### Environment Manager

```bash
# Configurar entorno específico
./scripts/env-manager.sh setup development
./scripts/env-manager.sh setup testing
./scripts/env-manager.sh setup production

# Controlar servicios
./scripts/env-manager.sh start development
./scripts/env-manager.sh stop development
./scripts/env-manager.sh restart development

# Monitoreo
./scripts/env-manager.sh status development
./scripts/env-manager.sh logs development
./scripts/env-manager.sh logs development backend  # Logs específicos

# Limpieza
./scripts/env-manager.sh clean development
```

### Test Manager

```bash
# Configuración de testing
./scripts/test-manager.sh setup

# Ejecución de tests
./scripts/test-manager.sh unit --coverage
./scripts/test-manager.sh integration --backend-only
./scripts/test-manager.sh e2e --verbose
./scripts/test-manager.sh all --fast

# Limpieza de testing
./scripts/test-manager.sh clean
```

## 📊 Configuraciones de Entorno

### Desarrollo (`config/.env.development`)
- Hot reload activado
- Debugging habilitado
- Puertos: Backend (8000), Frontend (5173), DB (5433)
- Mailcatcher para emails
- Logs detallados

### Testing (`config/.env.testing`)
- Base de datos aislada
- Cache separado
- Puertos: Backend (8001), Frontend (5174), DB (5434)
- Configuración optimizada para CI/CD
- Logs minimalistas

### Producción (`config/.env.production`)
- Seguridad maximizada
- Variables obligatorias
- SSL/TLS habilitado
- CORS restrictivo
- Monitoreo con Sentry

## 🔍 Troubleshooting

### Problemas Comunes

**Puerto ocupado:**
```bash
make stop
make clean
make setup
```

**Base de datos no conecta:**
```bash
./scripts/env-manager.sh logs development postgres
./scripts/env-manager.sh restart development
```

**Tests fallan:**
```bash
./scripts/test-manager.sh clean
./scripts/test-manager.sh setup
./scripts/test-manager.sh unit --verbose
```

**Containers no inician:**
```bash
docker system prune -f
make reset
```

### Logs Útiles

```bash
# Ver todos los logs
make logs

# Logs específicos por servicio
./scripts/env-manager.sh logs development backend
./scripts/env-manager.sh logs development frontend
./scripts/env-manager.sh logs development postgres

# Logs de testing
./scripts/env-manager.sh logs testing
```

## 🎯 Mejoras Implementadas

### ✅ Simplificación
- Un solo comando por tarea principal
- Scripts unificados para gestión
- Configuraciones centralizadas
- Makefile autodocumentado

### ✅ Organización
- Archivos .env separados por entorno
- Docker compose modular
- Scripts con responsabilidades claras
- Documentación integrada

### ✅ Robustez
- Validación de entornos
- Manejo de errores mejorado
- Cleanup automático
- Health checks optimizados

### ✅ Desarrollo
- Hot reload automático
- Debugging simplificado
- Ports no conflictivos
- Tools integrados

### ✅ Testing
- Entorno completamente aislado
- Tests paralelos
- Cobertura automática
- CI/CD optimizado

## 📈 Próximos Pasos

1. **Migrar configuración actual** a nueva estructura
2. **Actualizar CI/CD** para usar nuevos scripts
3. **Documentar workflows** específicos del equipo
4. **Capacitar equipo** en nuevos comandos
5. **Monitorear uso** y optimizar según feedback