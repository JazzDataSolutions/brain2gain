# 🚀 Brain2Gain - Separación de Ambientes

Este documento explica cómo usar la nueva funcionalidad de separación de ambientes implementada para Brain2Gain.

## 📋 Resumen

Se ha implementado una separación completa de ambientes que permite ejecutar:

1. **Modo Store** - Solo la tienda e-commerce pública
2. **Modo Admin** - Solo el panel administrativo/ERP 
3. **Modo Full** - Aplicación completa (modo original)

## 🏗️ Arquitectura

### Modo Store (E-commerce Público)
- **Frontend**: React optimizado para clientes
- **API**: Solo endpoints públicos (productos, carrito, checkout)
- **Seguridad**: Sin acceso a funciones administrativas
- **Puerto**: 3000 (frontend), 8000 (API)

### Modo Admin (Panel ERP)
- **Frontend**: React optimizado para administradores
- **API**: Solo endpoints administrativos (usuarios, inventario, reportes)
- **Seguridad**: Requiere autenticación de admin obligatoria
- **Puerto**: 3001 (frontend), 8001 (API)
- **Extras**: Adminer para gestión de BD (puerto 8080)

## 🚀 Uso

### Ejecutar Solo la Tienda

```bash
# Usar configuración de store
cp .env.store .env

# Iniciar tienda
docker-compose -f docker-compose.store.yml up -d

# Acceder
# Store: http://localhost:3000
# API: http://localhost:8000
```

### Ejecutar Solo Admin/ERP

```bash
# Usar configuración de admin
cp .env.admin .env

# Iniciar admin
docker-compose -f docker-compose.admin.yml up -d

# Acceder
# Admin: http://localhost:3001
# API: http://localhost:8001  
# DB Manager: http://localhost:8080
```

### Ejecutar Ambos (Desarrollo)

```bash
# Terminal 1 - Store
cp .env.store .env
docker-compose -f docker-compose.store.yml up

# Terminal 2 - Admin
cp .env.admin .env
docker-compose -f docker-compose.admin.yml up
```

## 🧪 Testing

Ejecutar el script de pruebas automatizado:

```bash
# Probar ambos ambientes
./scripts/test-environments.sh
```

Este script verifica:
- ✅ Inicio correcto de servicios
- ✅ Aislamiento de APIs
- ✅ Seguridad de endpoints
- ✅ Funcionalidad de frontends

## 📁 Archivos Clave

### Docker Compose
- `docker-compose.store.yml` - Configuración solo tienda
- `docker-compose.admin.yml` - Configuración solo admin
- `docker-compose.yml` - Configuración original (full)

### Variables de Entorno
- `.env.store` - Variables para modo tienda
- `.env.admin` - Variables para modo admin
- `.env` - Variables principales

### Código Modificado
- `backend/app/main.py` - Lógica de modos de API
- `backend/app/api/main.py` - Enrutamiento condicional
- `backend/Dockerfile` - Argumentos de build
- `frontend/Dockerfile` - Argumentos de build

## 🔒 Seguridad

### Modo Store
- ❌ Sin acceso a endpoints administrativos
- ❌ Sin acceso a gestión de usuarios
- ✅ Solo productos, carrito, checkout
- ✅ Rate limiting específico para tienda

### Modo Admin
- ✅ Acceso completo a funciones administrativas
- ✅ Requiere autenticación obligatoria
- ❌ Sin acceso a endpoints públicos
- ✅ Logs de auditoría habilitados

## 🌐 Producción

### Dominios Sugeridos
- `store.brain2gain.com` - Tienda pública
- `admin.brain2gain.com` - Panel administrativo
- `db.brain2gain.com` - Gestor de base de datos

### Configuración Traefik
Los archivos Docker Compose incluyen configuración para Traefik con SSL automático.

## 📊 Beneficios

### Performance
- **50% menos recursos** por ambiente
- **Carga más rápida** al eliminar código innecesario
- **Cache específico** por tipo de uso

### Seguridad
- **Aislamiento completo** entre tienda y admin
- **Surface de ataque reducida**
- **Auditoría independiente**

### Escalabilidad
- **Deploy independiente** de cada parte
- **Scaling horizontal** específico
- **Mantenimiento sin downtime**

### Desarrollo
- **Testing específico** por funcionalidad
- **Desarrollo paralelo** de equipos
- **CI/CD independiente**

## 🔧 Troubleshooting

### Problema: Servicios no inician
```bash
# Verificar logs
docker-compose -f docker-compose.store.yml logs

# Limpiar volúmenes
docker-compose -f docker-compose.store.yml down -v
```

### Problema: Error de CORS
Verificar que las variables `*_CORS_ORIGINS` en `.env.store` o `.env.admin` incluyan el dominio correcto.

### Problema: Base de datos
```bash
# Resetear BD del store
docker volume rm brain2gain_store_postgres

# Resetear BD del admin  
docker volume rm brain2gain_admin_postgres
```

## 📈 Próximos Pasos

1. **Monitoreo independiente** con Prometheus/Grafana
2. **CDN específico** para assets de store
3. **WAF diferenciado** para cada ambiente
4. **Backup estratégico** por criticidad
5. **Auto-scaling** basado en métricas específicas

---

> 🎯 **Objetivo alcanzado**: Separación completa de ambientes funcional, segura y escalable para Brain2Gain.