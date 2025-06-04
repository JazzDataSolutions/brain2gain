# Wireframe: Catálogo de Productos

## Layout Principal

```
┌─────────────────────────────────────────────────────────────┐
│                        HEADER                               │
│  [Logo] [Navegación] [Búsqueda] [Login/Usuario] [Carrito]  │
└─────────────────────────────────────────────────────────────┘

┌─────────────┬───────────────────────────────────────────────┐
│             │                                               │
│   FILTROS   │              GRID DE PRODUCTOS                │
│             │                                               │
│ Categorías  │  ┌─────────┬─────────┬─────────┬─────────┐   │
│ □ Proteínas │  │[Imagen] │[Imagen] │[Imagen] │[Imagen] │   │
│ □ Creatinas │  │ Nombre  │ Nombre  │ Nombre  │ Nombre  │   │
│ □ Pre-Work  │  │ $Precio │ $Precio │ $Precio │ $Precio │   │
│             │  │[+ Cart] │[+ Cart] │[+ Cart] │[+ Cart] │   │
│ Precio      │  └─────────┴─────────┴─────────┴─────────┘   │
│ [$] - [$$$] │                                               │
│             │  ┌─────────┬─────────┬─────────┬─────────┐   │
│ Marca       │  │[Imagen] │[Imagen] │[Imagen] │[Imagen] │   │
│ □ Optimum   │  │ Nombre  │ Nombre  │ Nombre  │ Nombre  │   │
│ □ MuscleTech│  │ $Precio │ $Precio │ $Precio │ $Precio │   │
│ □ Dymatize  │  │[+ Cart] │[+ Cart] │[+ Cart] │[+ Cart] │   │
│             │  └─────────┴─────────┴─────────┴─────────┘   │
│ [Limpiar]   │                                               │
│             │           [ < ] [1] [2] [3] [ > ]             │
└─────────────┴───────────────────────────────────────────────┘
```

## Componentes Detallados

### Header
- **Logo**: Enlace a homepage
- **Navegación**: Catálogo, Ofertas, Nosotros, Contacto
- **Búsqueda**: Campo de texto con autocomplete
- **Login/Usuario**: Botón de login o menú de usuario
- **Carrito**: Icono con contador de items

### Sidebar de Filtros
- **Categorías**: Checkboxes con conteo de productos
- **Rango de Precio**: Slider dual para min/max
- **Marcas**: Checkboxes con marcas populares
- **Stock**: Solo disponibles
- **Botón Limpiar**: Reset todos los filtros

### Card de Producto
```
┌─────────────────┐
│                 │
│     [IMAGEN]    │
│                 │
├─────────────────┤
│ Nombre Producto │
│ $XX.XX          │
│ ⭐⭐⭐⭐⭐ (reviews) │
│                 │
│  [Agregar +]    │
└─────────────────┘
```

### Estados Interactivos
- **Hover**: Sombra y botón destacado
- **Loading**: Skeleton cards mientras carga
- **Sin resultados**: Mensaje con sugerencias
- **Error**: Mensaje de error con botón retry

## Responsive Behavior

### Desktop (>1024px)
- 4 columnas en grid
- Sidebar visible
- Header completo

### Tablet (768px - 1024px)
- 3 columnas en grid
- Sidebar colapsable
- Header compacto

### Mobile (<768px)
- 2 columnas en grid
- Filtros en modal/drawer
- Header minimalista

## Interacciones

1. **Filtrado**: Aplicación inmediata sin recargar página
2. **Paginación**: Carga infinita o paginación tradicional
3. **Ordenamiento**: Dropdown con opciones (precio, popularidad, nuevo)
4. **Añadir al carrito**: Feedback visual + actualización contador
5. **Vista rápida**: Modal con detalles sin salir del catálogo