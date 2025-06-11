# 🧪 Guía de Testing - Fases 1 y 2

Esta guía te ayudará a probar las implementaciones de las Fases 1 (Optimización BD + Cache Redis) y Fase 2 (Separación Frontend).

## 📋 Pre-requisitos

Antes de comenzar las pruebas, asegúrate de tener:

```bash
# Verificar versiones requeridas
docker --version     # >= 20.0
docker-compose --version  # >= 1.27
node --version       # >= 20.0
python --version     # >= 3.10
```

## 🚀 Paso 1: Levantar el Entorno

### 1.1 Configuración Inicial
```bash
cd /home/jazzzfm/Documents/Brain2Gain/brain2gain

# Verificar que existe el archivo .env
ls -la .env

# Si no existe, crear desde el ejemplo
cp .env.example .env
```

### 1.2 Levantar los Servicios
```bash
# Levantar PostgreSQL y Redis
docker-compose -f docker-compose.dev.yml up postgres redis -d

# Verificar que los servicios están funcionando
docker-compose -f docker-compose.dev.yml ps

# Verificar logs
docker-compose -f docker-compose.dev.yml logs postgres
docker-compose -f docker-compose.dev.yml logs redis
```

### 1.3 Verificar Conectividad
```bash
# Test PostgreSQL connection
docker exec -it brain2gain-postgres-1 psql -U brain2gain_owner -d brain2gain_prod -c "SELECT version();"

# Test Redis connection
docker exec -it brain2gain-redis-1 redis-cli -a RedisPass2025 ping
```

## 🗄️ Paso 2: Testing de Base de Datos (Fase 1)

### 2.1 Aplicar Migraciones
```bash
cd backend

# Instalar dependencias (si no están instaladas)
pip install -r requirements-dev.txt

# Aplicar migraciones
alembic upgrade head

# Verificar que las migraciones se aplicaron
alembic current
alembic history --verbose
```

### 2.2 Verificar Índices Creados
```bash
# Conectar a PostgreSQL y verificar índices
docker exec -it brain2gain-postgres-1 psql -U brain2gain_owner -d brain2gain_prod

# En la consola de PostgreSQL:
\di  -- Listar todos los índices

# Verificar índices específicos creados en Fase 1:
SELECT indexname, tablename, indexdef 
FROM pg_indexes 
WHERE indexname LIKE 'idx_%' 
ORDER BY tablename, indexname;

# Verificar vista materializada
\dv  -- Listar vistas materializadas
SELECT * FROM mv_top_products LIMIT 5;
```

### 2.3 Testing de Performance
```bash
# En PostgreSQL, probar queries optimizados:

-- Test índice de productos activos
EXPLAIN ANALYZE 
SELECT * FROM product WHERE status = 'ACTIVE';

-- Test índice de pedidos por cliente
EXPLAIN ANALYZE 
SELECT * FROM salesorder 
WHERE customer_id = 1 
ORDER BY order_date DESC;

-- Test función de productos top
SELECT * FROM get_top_products(10);
```

## 🔄 Paso 3: Testing de Redis Cache (Fase 1)

### 3.1 Levantar Backend
```bash
cd backend

# Levantar el backend con las nuevas configuraciones
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3.2 Verificar Cache en Acción
```bash
# En otra terminal, monitorear Redis
docker exec -it brain2gain-redis-1 redis-cli -a RedisPass2025 monitor

# Hacer requests al API para ver el cache funcionando
curl http://localhost:8000/api/v1/items/

# En el monitor de Redis deberías ver:
# 1. Primer request: MISS + SET (guarda en cache)
# 2. Segundo request: GET (lee desde cache)
```

### 3.3 Testing Manual del Cache
```bash
# Conectar a Redis directamente
docker exec -it brain2gain-redis-1 redis-cli -a RedisPass2025

# Ver todas las keys de cache
keys products:*

# Ver contenido de una key específica
get "products:list:0:100"

# Ver estadísticas de cache
info stats
```

## 🎨 Paso 4: Testing Frontend (Fase 2)

### 4.1 Instalar Dependencias
```bash
cd frontend

# Instalar dependencias
npm install

# Verificar que no hay errores de dependencias
npm ls --depth=0
```

### 4.2 Levantar Frontend
```bash
# Levantar en modo desarrollo
npm run dev

# El frontend estará disponible en:
# http://localhost:5173
```

### 4.3 Testing de Rutas

#### Rutas de Tienda (Públicas)
```
✅ http://localhost:5173/           → Redirige a /store
✅ http://localhost:5173/store      → Landing de tienda
✅ http://localhost:5173/store/products → Catálogo de productos
✅ http://localhost:5173/store/cart     → Carrito de compras
✅ http://localhost:5173/store/checkout → Proceso de checkout
```

#### Rutas de Admin (Protegidas)
```
✅ http://localhost:5173/admin          → Dashboard admin (requiere login)
✅ http://localhost:5173/admin/inventory → Gestión de inventario
✅ http://localhost:5173/admin/orders   → Gestión de pedidos
✅ http://localhost:5173/admin/customers → Gestión de clientes
✅ http://localhost:5173/admin/reports  → Reportes y analytics
```

### 4.4 Testing de Funcionalidades

#### Store Testing
1. **Navegación**: Verificar que el navbar funciona correctamente
2. **Búsqueda**: Probar la barra de búsqueda (aunque esté mock)
3. **Carrito**: 
   - Agregar productos al carrito
   - Ver contador del carrito en navbar
   - Ir a página de carrito
   - Modificar cantidades
   - Eliminar productos
4. **Persistencia**: Recargar página y verificar que el carrito persiste
5. **Checkout**: Navegar al proceso de checkout

#### Admin Testing
1. **Autenticación**: Intentar acceder sin login (debe redirigir)
2. **Login**: Hacer login con credenciales admin
3. **Dashboard**: Verificar que se muestra el dashboard
4. **Navegación**: Probar sidebar y navegación entre secciones
5. **Notificaciones**: Verificar dropdown de notificaciones

## 🔗 Paso 5: Testing de Integración

### 5.1 Integración Backend-Frontend
```bash
# Con backend y frontend funcionando:

# 1. Verificar que el frontend consume la API
# Abrir DevTools → Network tab
# Navegar a /store/products
# Deberías ver request a: http://localhost:8000/api/v1/items/

# 2. Verificar cache en acción
# En Redis monitor, hacer el mismo request dos veces
# Primera vez: Miss + Set
# Segunda vez: Solo Get
```

### 5.2 Testing de Performance
```bash
# Medir tiempos de respuesta

# Sin cache (primera carga)
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/v1/items/

# Con cache (segunda carga)
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/v1/items/

# Crear curl-format.txt:
echo '     time_namelookup:  %{time_namelookup}\n
        time_connect:  %{time_connect}\n
     time_appconnect:  %{time_appconnect}\n
    time_pretransfer:  %{time_pretransfer}\n
       time_redirect:  %{time_redirect}\n
  time_starttransfer:  %{time_starttransfer}\n
                     ----------\n
          time_total:  %{time_total}\n' > curl-format.txt
```

## 🐛 Problemas Comunes y Soluciones

### Backend Issues

**Error: Redis connection failed**
```bash
# Verificar que Redis está funcionando
docker-compose -f docker-compose.dev.yml logs redis

# Reiniciar Redis
docker-compose -f docker-compose.dev.yml restart redis
```

**Error: Database migration failed**
```bash
# Verificar conexión a BD
docker exec -it brain2gain-postgres-1 psql -U brain2gain_owner -d brain2gain_prod -c "SELECT 1;"

# Reset migraciones si es necesario
alembic downgrade base
alembic upgrade head
```

### Frontend Issues

**Error: Module not found**
```bash
# Limpiar node_modules y reinstalar
rm -rf node_modules package-lock.json
npm install
```

**Error: API calls failing**
```bash
# Verificar CORS en backend logs
# Verificar que backend está en puerto 8000
# Verificar variables de entorno VITE_API_URL
```

### Integration Issues

**Frontend no muestra datos**
```bash
# 1. Verificar Network tab en DevTools
# 2. Verificar que ItemsService existe en cliente API
# 3. Verificar formato de respuesta de API
```

## ✅ Checklist de Verificación

### Fase 1 - Backend Optimizado
- [ ] PostgreSQL funcionando correctamente
- [ ] Redis funcionando correctamente
- [ ] Migraciones aplicadas exitosamente
- [ ] Índices creados correctamente
- [ ] Vista materializada funcional
- [ ] Cache funcionando en ProductService
- [ ] Tiempos de respuesta mejorados

### Fase 2 - Frontend Separado
- [ ] Rutas /store/* funcionando
- [ ] Rutas /admin/* funcionando
- [ ] Layouts diferenciados
- [ ] Navegación entre contextos
- [ ] Store cart funcionando
- [ ] Persistencia de carrito
- [ ] Autenticación admin funcional

### Integración
- [ ] Frontend consume API correctamente
- [ ] Cache se refleja en performance
- [ ] Separación de contextos funcional
- [ ] No hay errores en consola
- [ ] Performance mejorada vs estado inicial

## 📊 Métricas Esperadas

Si todo funciona correctamente, deberías observar:

**Performance Backend:**
- Respuesta API sin cache: ~200-500ms
- Respuesta API con cache: ~50-100ms
- Queries BD optimizadas: ~10-50ms

**Performance Frontend:**
- Carga inicial: <2s
- Navegación entre rutas: <500ms
- Actualizaciones de carrito: <100ms

**Funcionalidad:**
- Cache hit rate: >70% después de uso normal
- Separación clara entre store/admin
- Persistencia de estado entre sesiones