# 🚀 Mejoras Inmediatas para Brain2Gain

## 🎯 Acciones de Alto Impacto (Implementables en 1-2 semanas)

### 1. Separación de Rutas Frontend (2-3 días)

```typescript
// Estructura propuesta en frontend/src/routes/
├── store/              # Rutas públicas de la tienda
│   ├── _layout.tsx     # Layout con navbar de tienda
│   ├── index.tsx       # Home de productos
│   ├── products/       # Catálogo
│   ├── cart/           # Carrito
│   └── checkout/       # Proceso de compra
│
├── admin/              # Rutas del ERP (requiere auth)
│   ├── _layout.tsx     # Layout con sidebar admin
│   ├── dashboard/      # Dashboard principal
│   ├── inventory/      # Gestión de inventario
│   ├── orders/         # Gestión de pedidos
│   ├── customers/      # CRM
│   └── reports/        # Reportes y analytics
│
└── auth/               # Autenticación compartida
```

### 2. Optimización de Base de Datos (1 día)

```sql
-- Índices críticos para performance
CREATE INDEX idx_products_status_active ON products(status) WHERE status = 'active';
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_orders_customer_date ON orders(customer_id, created_at DESC);
CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_inventory_product_sku ON inventory(product_id, sku);

-- Vista materializada para productos más vendidos
CREATE MATERIALIZED VIEW mv_top_products AS
SELECT 
    p.product_id,
    p.name,
    p.sku,
    COUNT(oi.order_item_id) as total_sold,
    SUM(oi.quantity) as units_sold,
    SUM(oi.quantity * oi.unit_price) as revenue
FROM products p
JOIN order_items oi ON p.product_id = oi.product_id
JOIN orders o ON oi.order_id = o.order_id
WHERE o.created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY p.product_id, p.name, p.sku
ORDER BY revenue DESC;

-- Refresh automático cada hora
CREATE OR REPLACE FUNCTION refresh_top_products()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_top_products;
END;
$$ LANGUAGE plpgsql;
```

### 3. Implementación de Cache con Redis (2 días)

```python
# backend/app/core/cache.py
from functools import wraps
import json
import redis
from typing import Optional, Any
from app.core.config import settings

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

def cache_key_wrapper(prefix: str, ttl: int = 300):
    """Decorator para cachear resultados de funciones"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generar key única basada en argumentos
            cache_key = f"{prefix}:{':'.join(map(str, args))}:{json.dumps(kwargs, sort_keys=True)}"
            
            # Intentar obtener de cache
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Ejecutar función y cachear resultado
            result = await func(*args, **kwargs)
            redis_client.setex(cache_key, ttl, json.dumps(result, default=str))
            
            return result
        return wrapper
    return decorator

# Uso en servicios
class ProductService:
    @cache_key_wrapper("products:list", ttl=300)  # 5 minutos
    async def list_active_products(self, skip: int = 0, limit: int = 50):
        # Lógica actual...
        pass
    
    @cache_key_wrapper("products:detail", ttl=600)  # 10 minutos
    async def get_product_by_id(self, product_id: int):
        # Lógica actual...
        pass
    
    async def update_product(self, product_id: int, data: dict):
        # Actualizar producto
        result = await self._update_product(product_id, data)
        
        # Invalidar caches relacionados
        redis_client.delete(f"products:detail:{product_id}")
        for key in redis_client.scan_iter("products:list:*"):
            redis_client.delete(key)
        
        return result
```

### 4. API Rate Limiting (1 día)

```python
# backend/app/middlewares/rate_limit.py
from fastapi import Request, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address
import redis

# Configurar limiter con Redis
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.REDIS_URL
)

# Diferentes límites por tipo de usuario
def get_rate_limit_key(request: Request):
    user = getattr(request.state, "user", None)
    if user:
        if user.role == "admin":
            return f"admin:{user.id}"
        return f"user:{user.id}"
    return get_remote_address(request)

# Aplicar en rutas
@router.get("/products")
@limiter.limit("100/minute", key_func=get_rate_limit_key)  # Usuarios autenticados
@limiter.limit("20/minute")  # Por IP
async def list_products():
    pass

@router.post("/orders")
@limiter.limit("10/hour", key_func=get_rate_limit_key)  # Prevenir spam de pedidos
async def create_order():
    pass
```

### 5. Separación de Ambientes con Docker Compose (1 día)

```yaml
# docker-compose.store.yml - Solo tienda
version: '3.8'
services:
  store-frontend:
    build:
      context: ./frontend
      args:
        - VITE_APP_MODE=store
    environment:
      - VITE_API_URL=${API_URL}
      - VITE_ENABLE_ADMIN=false
    ports:
      - "3000:80"
    
  api:
    build: ./backend
    environment:
      - API_MODE=public
      - ENABLE_ADMIN_ROUTES=false
    ports:
      - "8000:8000"

# docker-compose.admin.yml - Solo ERP/Admin
version: '3.8'
services:
  admin-frontend:
    build:
      context: ./frontend
      args:
        - VITE_APP_MODE=admin
    environment:
      - VITE_API_URL=${API_URL}
      - VITE_ENABLE_STORE=false
    ports:
      - "3001:80"
    
  api:
    build: ./backend
    environment:
      - API_MODE=admin
      - REQUIRE_ADMIN_AUTH=true
    ports:
      - "8001:8000"
```

### 6. Mejoras de UX Inmediatas (3-4 días)

```typescript
// frontend/src/features/store/QuickCart.tsx
// Mini carrito flotante para mejorar conversión

import { useCartStore } from '@/stores/cartStore';
import { motion, AnimatePresence } from 'framer-motion';

export function QuickCart() {
  const { items, total, isOpen } = useCartStore();
  
  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ x: 400, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: 400, opacity: 0 }}
          className="fixed right-4 top-20 w-96 bg-white shadow-2xl rounded-lg p-6 z-50"
        >
          <h3 className="font-bold text-lg mb-4">Tu Carrito</h3>
          
          {/* Items con scroll */}
          <div className="max-h-96 overflow-y-auto">
            {items.map(item => (
              <CartItemMini key={item.id} item={item} />
            ))}
          </div>
          
          {/* Total y acciones */}
          <div className="border-t pt-4 mt-4">
            <div className="flex justify-between mb-4">
              <span className="font-semibold">Total:</span>
              <span className="text-xl font-bold">${total}</span>
            </div>
            
            <div className="space-y-2">
              <Button 
                fullWidth 
                variant="primary"
                onClick={() => navigate('/checkout')}
              >
                Finalizar Compra
              </Button>
              
              <Button 
                fullWidth 
                variant="ghost"
                onClick={() => navigate('/cart')}
              >
                Ver Carrito Completo
              </Button>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

// Búsqueda instantánea con Algolia/ElasticSearch
export function InstantSearch() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  
  // Debounced search
  const searchProducts = useMemo(
    () => debounce(async (q: string) => {
      if (q.length < 2) return;
      
      setLoading(true);
      const data = await api.products.search(q);
      setResults(data);
      setLoading(false);
    }, 300),
    []
  );
  
  return (
    <Command className="relative">
      <CommandInput 
        placeholder="Buscar proteínas, creatina..."
        value={query}
        onValueChange={(q) => {
          setQuery(q);
          searchProducts(q);
        }}
      />
      
      <CommandList>
        {loading && <CommandLoading />}
        
        {results.length > 0 && (
          <CommandGroup heading="Productos">
            {results.map(product => (
              <CommandItem
                key={product.id}
                onSelect={() => navigate(`/products/${product.id}`)}
              >
                <img 
                  src={product.thumbnail} 
                  className="w-10 h-10 object-cover rounded mr-3"
                />
                <div className="flex-1">
                  <div className="font-medium">{product.name}</div>
                  <div className="text-sm text-gray-500">${product.price}</div>
                </div>
              </CommandItem>
            ))}
          </CommandGroup>
        )}
      </CommandList>
    </Command>
  );
}
```

### 7. Analytics y Métricas (2 días)

```python
# backend/app/services/analytics_service.py
from datetime import datetime, timedelta
from sqlalchemy import func
from app.models import Order, OrderItem, Product

class AnalyticsService:
    async def get_dashboard_metrics(self, date_from: datetime, date_to: datetime):
        """Métricas principales para dashboard"""
        
        # Ventas totales
        total_sales = await self.session.scalar(
            select(func.sum(Order.total_amount))
            .where(Order.created_at.between(date_from, date_to))
            .where(Order.status == 'completed')
        )
        
        # Número de pedidos
        total_orders = await self.session.scalar(
            select(func.count(Order.id))
            .where(Order.created_at.between(date_from, date_to))
        )
        
        # Ticket promedio
        avg_order_value = total_sales / total_orders if total_orders > 0 else 0
        
        # Productos más vendidos (usar vista materializada)
        top_products = await self.session.execute(
            text("SELECT * FROM mv_top_products LIMIT 10")
        )
        
        # Métricas de conversión
        visitors = await self.get_unique_visitors(date_from, date_to)
        conversion_rate = (total_orders / visitors * 100) if visitors > 0 else 0
        
        return {
            "period": {
                "from": date_from.isoformat(),
                "to": date_to.isoformat()
            },
            "sales": {
                "total": float(total_sales or 0),
                "orders": total_orders,
                "avg_order_value": float(avg_order_value),
                "conversion_rate": float(conversion_rate)
            },
            "top_products": [
                {
                    "id": p.product_id,
                    "name": p.name,
                    "units_sold": p.units_sold,
                    "revenue": float(p.revenue)
                }
                for p in top_products
            ],
            "trends": await self.calculate_trends(date_from, date_to)
        }
    
    @cache_key_wrapper("analytics:trends", ttl=3600)
    async def calculate_trends(self, date_from: datetime, date_to: datetime):
        """Calcular tendencias vs período anterior"""
        period_length = (date_to - date_from).days
        previous_from = date_from - timedelta(days=period_length)
        previous_to = date_from
        
        current_sales = await self._get_period_sales(date_from, date_to)
        previous_sales = await self._get_period_sales(previous_from, previous_to)
        
        growth = ((current_sales - previous_sales) / previous_sales * 100) if previous_sales > 0 else 0
        
        return {
            "sales_growth": float(growth),
            "is_positive": growth > 0,
            "period_comparison": f"vs últimos {period_length} días"
        }
```

### 8. Notificaciones en Tiempo Real (2 días)

```python
# backend/app/services/notification_service.py
from app.core.websocket import manager
import asyncio

class NotificationService:
    async def notify_order_status(self, order_id: int, status: str):
        """Notificar cambios de estado de pedido"""
        order = await self.get_order(order_id)
        
        # Notificación al cliente
        await manager.send_personal_message(
            f"Tu pedido #{order.number} está {status}",
            order.customer_id
        )
        
        # Notificación al admin
        await manager.broadcast_to_role(
            f"Nuevo pedido #{order.number} - {status}",
            role="admin"
        )
        
        # Email asíncrono
        asyncio.create_task(
            self.send_order_email(order, status)
        )
    
    async def notify_low_stock(self, product: Product):
        """Alertar cuando el stock está bajo"""
        if product.stock <= product.min_stock:
            message = f"⚠️ Stock bajo: {product.name} - Quedan {product.stock} unidades"
            
            await manager.broadcast_to_role(message, role="admin")
            await self.send_slack_alert(message)
```

## 📊 Métricas de Éxito Esperadas

### Semana 1:
- **-50% tiempo de carga** (de 3s a 1.5s)
- **+20% conversión** en carrito
- **-70% queries a BD** (con cache)

### Mes 1:
- **+35% velocidad checkout**
- **+15% ticket promedio** (recomendaciones)
- **-80% errores** en producción

### Mes 3:
- **2x capacidad** de pedidos/día
- **+40% satisfacción** del cliente (NPS)
- **ROI positivo** de la inversión

## 🚀 Orden de Implementación Recomendado

1. **Día 1-2**: Cache con Redis + Índices DB
2. **Día 3-4**: Separación de rutas frontend
3. **Día 5-6**: Rate limiting + Seguridad
4. **Día 7-8**: Analytics dashboard
5. **Día 9-10**: Optimizaciones UX
6. **Día 11-14**: Testing y ajustes

---

*Estas mejoras son 100% compatibles con la arquitectura actual y sientan las bases para la migración futura a microservicios.*