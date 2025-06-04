# Wireframe: Carrito de Compras

## Layout Principal

```
┌─────────────────────────────────────────────────────────────┐
│                        HEADER                               │
│  [Logo] [Navegación] [Búsqueda] [Login/Usuario] [Carrito]  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                     CARRITO DE COMPRAS                     │
│                                                             │
│ ┌─────────────────────────────────┬─────────────────────────┐ │
│ │           PRODUCTOS             │       RESUMEN          │ │
│ │                                 │                         │ │
│ │ ┌─────────────────────────────┐ │  Subtotal: $XXX.XX     │ │
│ │ │[IMG] Producto 1             │ │  Envío:    $XX.XX      │ │
│ │ │     Precio: $XX.XX          │ │  Impuestos: $XX.XX     │ │
│ │ │     [−] [2] [+] [🗑️]        │ │  ─────────────────     │ │
│ │ └─────────────────────────────┘ │  TOTAL:    $XXX.XX     │ │
│ │                                 │                         │ │
│ │ ┌─────────────────────────────┐ │  [Código Descuento]    │ │
│ │ │[IMG] Producto 2             │ │  [Aplicar]             │ │
│ │ │     Precio: $XX.XX          │ │                         │ │
│ │ │     [−] [1] [+] [🗑️]        │ │  [Continuar Comprando] │ │
│ │ └─────────────────────────────┘ │                         │ │
│ │                                 │  [PROCEDER AL PAGO]    │ │
│ │ [+ Seguir Comprando]            │                         │ │
│ └─────────────────────────────────┴─────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Card de Producto en Carrito

```
┌─────────────────────────────────────────────────────────────┐
│ ┌─────┐  Whey Protein Gold Standard                         │
│ │     │  100% Whey Protein Isolate - Chocolate              │
│ │ IMG │  SKU: WP-001                                        │
│ │     │                                                     │
│ └─────┘  Precio unitario: $45.99                           │
│                                                             │
│          Cantidad:  [−] [2] [+]    Subtotal: $91.98       │
│                                                             │
│          [🗑️ Eliminar]              [💾 Guardar p/después] │
└─────────────────────────────────────────────────────────────┘
```

## Panel Resumen

```
┌─────────────────────────┐
│       RESUMEN           │
├─────────────────────────┤
│ Subtotal:    $150.00    │
│ Envío:       $12.99     │
│ Impuestos:   $15.00     │
│ ─────────────────────   │
│ TOTAL:       $177.99    │
├─────────────────────────┤
│ Código de Descuento:    │
│ [_______________] [OK]  │
├─────────────────────────┤
│ Tiempo estimado:        │
│ 📦 2-3 días hábiles     │
├─────────────────────────┤
│ [Continuar Comprando]   │
│                         │
│ [PROCEDER AL PAGO] 🔒   │
└─────────────────────────┘
```

## Estados de Carrito

### Carrito Vacío
```
┌─────────────────────────────────────┐
│             🛒                      │
│        Tu carrito está vacío        │
│                                     │
│   ¡Descubre nuestros productos!    │
│                                     │
│      [Ver Catálogo]                │
└─────────────────────────────────────┘
```

### Loading States
- **Actualizando cantidad**: Spinner en controles +/-
- **Eliminando producto**: Fade out animation
- **Aplicando descuento**: Loading en botón "Aplicar"

## Interacciones

### Gestión de Cantidad
1. **Botones +/-**: Actualización inmediata con debounce
2. **Input directo**: Validación min/max stock
3. **Stock insuficiente**: Mensaje de advertencia

### Códigos de Descuento
1. **Validación**: Verificar código en tiempo real
2. **Aplicación**: Actualizar totales automáticamente
3. **Error**: Mensaje claro si código inválido

### Persistencia
1. **Usuarios registrados**: Sincronizar con servidor
2. **Invitados**: LocalStorage con expiración
3. **Checkout abandonado**: Email recordatorio (usuarios registrados)

## Responsive Design

### Mobile (<768px)
```
┌─────────────────────┐
│      CARRITO        │
├─────────────────────┤
│ [IMG] Producto 1    │
│ Precio: $XX.XX      │
│ [−] [2] [+] [🗑️]    │
├─────────────────────┤
│ [IMG] Producto 2    │
│ Precio: $XX.XX      │
│ [−] [1] [+] [🗑️]    │
├─────────────────────┤
│                     │
│ Subtotal: $XXX.XX   │
│ Envío:    $XX.XX    │
│ Total:    $XXX.XX   │
│                     │
│ [PROCEDER AL PAGO]  │
└─────────────────────┘
```

### Tablet (768px - 1024px)
- Layout similar al desktop pero más compacto
- Resumen puede moverse abajo en portrait

## Validaciones y Errores

1. **Stock agotado**: Deshabilitar controles + mensaje
2. **Producto descontinuado**: Opción de eliminar + sugerencias
3. **Error de red**: Retry automático + mensaje
4. **Límite de cantidad**: Mensaje informativo