# Wireframe: Proceso de Checkout

## Layout Principal - Paso a Paso

```
┌─────────────────────────────────────────────────────────────┐
│                        HEADER                               │
│  [Logo] [Navegación] [Búsqueda] [Login/Usuario] [Carrito]  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                       CHECKOUT                              │
│                                                             │
│ [1. Info Personal] → [2. Envío] → [3. Pago] → [4. Confirmar] │
│        ●               ○           ○          ○             │
└─────────────────────────────────────────────────────────────┘
```

## Paso 1: Información Personal

```
┌─────────────────────────────────────┬─────────────────────────┐
│          INFORMACIÓN PERSONAL       │       TU PEDIDO         │
│                                     │                         │
│ ┌─ Como invitado ──────────────────┐ │ ┌─────────────────────┐ │
│ │ Email: [___________________]     │ │ │ 2x Whey Protein     │ │
│ │ ☐ Crear cuenta                   │ │ │ 1x Creatina         │ │
│ └──────────────────────────────────┘ │ │ ───────────────     │ │
│                                     │ │ Subtotal: $150.00   │ │
│ ┌─ Ya tienes cuenta? ──────────────┐ │ │ Envío:    $12.99    │ │
│ │ [INICIAR SESIÓN]                 │ │ │ Total:    $162.99   │ │
│ └──────────────────────────────────┘ │ └─────────────────────┘ │
│                                     │                         │
│ Datos de facturación:               │ [Editar Carrito]        │
│ Nombre:    [___________________]    │                         │
│ Apellido:  [___________________]    │                         │
│ Teléfono:  [___________________]    │                         │
│ DNI/RUT:   [___________________]    │                         │
│                                     │                         │
│               [CONTINUAR]           │                         │
└─────────────────────────────────────┴─────────────────────────┘
```

## Paso 2: Información de Envío

```
┌─────────────────────────────────────┬─────────────────────────┐
│            DIRECCIÓN DE ENVÍO       │       TU PEDIDO         │
│                                     │                         │
│ ☐ Usar dirección de facturación     │ [Resumen del pedido]    │
│                                     │                         │
│ País:     [Chile        ▼]          │                         │
│ Región:   [Metropolitana▼]          │                         │
│ Comuna:   [Las Condes   ▼]          │                         │
│ Dirección:[___________________]     │                         │
│ Número:   [___] Depto: [_____]      │                         │
│ Código Postal: [_______]            │                         │
│                                     │                         │
│ ┌─ MÉTODO DE ENVÍO ─────────────────┐ │                         │
│ │ ○ Envío estándar (2-3 días) $12.99│ │                         │
│ │ ○ Envío express (1 día)   $24.99  │ │                         │
│ │ ○ Retiro en tienda        GRATIS  │ │                         │
│ └────────────────────────────────────┘ │                         │
│                                     │                         │
│      [← VOLVER]    [CONTINUAR]      │                         │
└─────────────────────────────────────┴─────────────────────────┘
```

## Paso 3: Método de Pago

```
┌─────────────────────────────────────┬─────────────────────────┐
│            MÉTODO DE PAGO           │       RESUMEN FINAL     │
│                                     │                         │
│ ┌─ TARJETA DE CRÉDITO/DÉBITO ──────┐ │ Subtotal:   $150.00     │
│ │ ○ Visa  ○ Mastercard  ○ Amex    │ │ Envío:      $12.99      │
│ │                                  │ │ Impuestos:  $0.00       │
│ │ Número: [____-____-____-____]    │ │ ─────────────────       │
│ │ Nombre: [___________________]    │ │ TOTAL:      $162.99     │
│ │ Vence:  [MM/AA] CVV: [___]      │ │                         │
│ └──────────────────────────────────┘ │ Método envío:           │
│                                     │ Envío estándar          │
│ ┌─ TRANSFERENCIA BANCARIA ─────────┐ │                         │
│ │ ○ Banco de Chile                 │ │ Dirección:              │
│ │ ○ Santander                      │ │ Las Condes, RM          │
│ │ ○ BCI                            │ │                         │
│ └──────────────────────────────────┘ │                         │
│                                     │                         │
│ ┌─ OTROS ──────────────────────────┐ │                         │
│ │ ○ PayPal                         │ │                         │
│ │ ○ Mercado Pago                   │ │                         │
│ │ ○ Webpay                         │ │                         │
│ └──────────────────────────────────┘ │                         │
│                                     │                         │
│      [← VOLVER]    [CONTINUAR]      │                         │
└─────────────────────────────────────┴─────────────────────────┘
```

## Paso 4: Confirmación

```
┌─────────────────────────────────────────────────────────────┐
│                    CONFIRMA TU PEDIDO                       │
│                                                             │
│ ┌─ REVISA TUS DATOS ─────────────────────────────────────┐   │
│ │ Email: usuario@ejemplo.com                            │   │
│ │ Teléfono: +56 9 1234 5678                            │   │
│ │ Dirección: Av. Las Condes 123, Las Condes, RM        │   │
│ │ Envío: Estándar (2-3 días)                           │   │
│ │ Pago: Visa ****1234                                  │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                             │
│ ┌─ PRODUCTOS ────────────────────────────────────────────┐   │
│ │ 2x Whey Protein Gold Standard          $91.98        │   │
│ │ 1x Creatina Monohydrate                $58.02        │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                             │
│ ┌─ TOTAL ────────────────────────────────────────────────┐   │
│ │ Subtotal:                              $150.00        │   │
│ │ Envío:                                 $12.99         │   │
│ │ Total:                                 $162.99        │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                             │
│ ☐ Acepto los términos y condiciones                        │
│ ☐ Acepto la política de privacidad                         │
│ ☐ Quiero recibir ofertas por email                         │
│                                                             │
│           [← VOLVER]    [CONFIRMAR PEDIDO] 🔒              │
└─────────────────────────────────────────────────────────────┘
```

## Página de Confirmación Exitosa

```
┌─────────────────────────────────────────────────────────────┐
│                         ✅                                  │
│                  ¡PEDIDO CONFIRMADO!                       │
│                                                             │
│              Número de pedido: #BG-2025-001234            │
│                                                             │
│ ┌─ DETALLES ─────────────────────────────────────────────┐   │
│ │ Total pagado: $162.99                                 │   │
│ │ Método de pago: Visa ****1234                         │   │
│ │ Envío estimado: 2-3 días hábiles                      │   │
│ │ Tracking: Se enviará por email                        │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                             │
│ 📧 Te hemos enviado la confirmación a usuario@ejemplo.com  │
│                                                             │
│        [VER PEDIDO]    [SEGUIR COMPRANDO]                  │
└─────────────────────────────────────────────────────────────┘
```

## Estados de Error

### Error de Pago
```
┌─────────────────────────────────────┐
│              ❌                     │
│         PAGO RECHAZADO              │
│                                     │
│ Tu tarjeta fue rechazada.           │
│ Por favor verifica los datos        │
│ o intenta con otro método.          │
│                                     │
│      [REINTENTAR]                   │
└─────────────────────────────────────┘
```

### Error de Stock
```
┌─────────────────────────────────────┐
│              ⚠️                      │
│        STOCK AGOTADO                │
│                                     │
│ Algunos productos ya no están       │
│ disponibles. Te hemos actualizado   │
│ el carrito.                         │
│                                     │
│      [VER CARRITO]                  │
└─────────────────────────────────────┘
```

## Responsive Design

### Mobile
- Un paso por pantalla
- Botones "Siguiente/Anterior" más grandes
- Resumen del pedido colapsable
- Formularios simplificados con menos campos por fila

### Validaciones en Tiempo Real
1. **Email**: Formato válido
2. **Teléfono**: Formato país específico
3. **Tarjeta**: Validación Luhn + CVV
4. **Código postal**: Formato válido para región