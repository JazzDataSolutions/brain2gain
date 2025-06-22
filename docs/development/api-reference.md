# 🔧 API Reference - Brain2Gain E-commerce Platform

## 📚 Overview

Brain2Gain provides a comprehensive REST API built with FastAPI, featuring automatic OpenAPI documentation, authentication, and full e-commerce functionality.

**Base URL**: `http://localhost:8000` (development)
**API Documentation**: `http://localhost:8000/docs` (Swagger UI)
**Alternative Docs**: `http://localhost:8000/redoc` (ReDoc)

## 🔐 Authentication

### JWT Authentication
The API uses JSON Web Tokens (JWT) for authentication with the following features:
- **Access Tokens**: Short-lived tokens for API access
- **Refresh Tokens**: Long-lived tokens for obtaining new access tokens
- **JTI Tracking**: Unique token IDs for security
- **Role-Based Access**: Different permissions per user role

#### Authentication Flow
```bash
# 1. Login to get tokens
POST /api/v1/login/access-token
{
  "username": "user@example.com",
  "password": "password"
}

# Response
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}

# 2. Use token in subsequent requests
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### User Roles
- **User**: Basic customer access
- **Admin**: Full administrative access
- **Manager**: Business management access
- **Seller**: Sales and inventory access
- **Accountant**: Financial access

## 📦 Core API Endpoints

### 🛍️ Products API

#### List Products
```http
GET /api/v1/products
```
**Parameters:**
- `skip` (int): Number of records to skip (default: 0)
- `limit` (int): Maximum records to return (default: 50)

**Response:**
```json
[
  {
    "product_id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "Whey Protein Premium",
    "description": "High-quality whey protein concentrate",
    "unit_price": 49.99,
    "sku": "WPP-001",
    "stock_quantity": 100,
    "status": "ACTIVE",
    "category": "Proteins"
  }
]
```

#### Get Product Details
```http
GET /api/v1/products/{product_id}
```

#### Create Product (Admin Only)
```http
POST /api/v1/products
Authorization: Bearer {token}
```
**Request Body:**
```json
{
  "name": "New Supplement",
  "description": "Product description",
  "unit_price": 29.99,
  "sku": "NS-001",
  "stock_quantity": 50,
  "category": "Supplements"
}
```

### 🛒 Shopping Cart API

#### Get User Cart
```http
GET /api/v1/cart
Authorization: Bearer {token}
```

#### Add Item to Cart
```http
POST /api/v1/cart/items
Authorization: Bearer {token}
```
**Request Body:**
```json
{
  "product_id": "123e4567-e89b-12d3-a456-426614174000",
  "quantity": 2
}
```

#### Update Cart Item
```http
PUT /api/v1/cart/items/{item_id}
Authorization: Bearer {token}
```
**Request Body:**
```json
{
  "quantity": 3
}
```

#### Remove Item from Cart
```http
DELETE /api/v1/cart/items/{item_id}
Authorization: Bearer {token}
```

### 📋 Orders API

#### Get My Orders
```http
GET /api/v1/orders/my-orders
Authorization: Bearer {token}
```
**Parameters:**
- `page` (int): Page number (default: 1)
- `page_size` (int): Items per page (default: 10)
- `status` (array): Filter by order status

#### Get Order Details
```http
GET /api/v1/orders/my-orders/{order_id}
Authorization: Bearer {token}
```

#### Checkout Flow

##### 1. Calculate Checkout
```http
POST /api/v1/orders/checkout/calculate
Authorization: Bearer {token}
```
**Request Body:**
```json
{
  "shipping_address": {
    "street": "123 Main St",
    "city": "Anytown",
    "state": "State",
    "postal_code": "12345",
    "country": "Country"
  },
  "payment_method": "stripe"
}
```

##### 2. Validate Checkout
```http
POST /api/v1/orders/checkout/validate
Authorization: Bearer {token}
```

##### 3. Confirm Checkout
```http
POST /api/v1/orders/checkout/confirm
Authorization: Bearer {token}
```
**Response:**
```json
{
  "order_id": "789e0123-e89b-12d3-a456-426614174000",
  "payment_required": true,
  "payment_intent_id": "pi_1234567890",
  "total_amount": 149.97
}
```

#### Cancel Order
```http
POST /api/v1/orders/{order_id}/cancel?reason=Customer requested cancellation
Authorization: Bearer {token}
```

### 💳 Payments API

#### Process Payment
```http
POST /api/v1/payments/process
Authorization: Bearer {token}
```
**Request Body:**
```json
{
  "payment_id": "payment_uuid",
  "stripe_payment_method_id": "pm_1234567890",
  "stripe_customer_id": "cus_1234567890"
}
```

#### Get Payment Methods
```http
GET /api/v1/payments/methods
```

#### Get My Payments
```http
GET /api/v1/payments/my-payments
Authorization: Bearer {token}
```

#### Get Payment Details
```http
GET /api/v1/payments/my-payments/{payment_id}
Authorization: Bearer {token}
```

### 👥 Users API

#### Get Current User
```http
GET /api/v1/users/me
Authorization: Bearer {token}
```

#### Update Profile
```http
PATCH /api/v1/users/me
Authorization: Bearer {token}
```
**Request Body:**
```json
{
  "full_name": "John Doe",
  "email": "john@example.com"
}
```

#### Change Password
```http
POST /api/v1/users/me/change-password
Authorization: Bearer {token}
```
**Request Body:**
```json
{
  "current_password": "current_password",
  "new_password": "new_password"
}
```

## 📊 Admin API Endpoints

### 🏢 Admin Orders Management

#### Get All Orders (Admin)
```http
GET /api/v1/orders
Authorization: Bearer {admin_token}
```
**Parameters:**
- `page` (int): Page number
- `page_size` (int): Items per page
- `status` (array): Filter by order status
- `payment_status` (array): Filter by payment status
- `search` (string): Search orders

#### Update Order Status (Admin)
```http
PATCH /api/v1/orders/{order_id}
Authorization: Bearer {admin_token}
```
**Request Body:**
```json
{
  "status": "SHIPPED",
  "tracking_number": "1234567890"
}
```

#### Get Order Statistics (Admin)
```http
GET /api/v1/orders/stats/overview
Authorization: Bearer {admin_token}
```

### 💰 Admin Payments Management

#### Get All Payments (Admin)
```http
GET /api/v1/payments
Authorization: Bearer {admin_token}
```

#### Create Refund (Admin)
```http
POST /api/v1/payments/refunds
Authorization: Bearer {admin_token}
```
**Request Body:**
```json
{
  "payment_id": "payment_uuid",
  "amount": 29.99,
  "reason": "Customer request"
}
```

#### Get Payment Statistics (Admin)
```http
GET /api/v1/payments/stats/overview
Authorization: Bearer {admin_token}
```

### 📈 Analytics API

#### Get Dashboard Metrics
```http
GET /api/v1/analytics/dashboard
Authorization: Bearer {admin_token}
```

#### Get Revenue Analytics
```http
GET /api/v1/analytics/revenue
Authorization: Bearer {admin_token}
```
**Parameters:**
- `period` (string): "daily", "weekly", "monthly", "yearly"
- `start_date` (date): Start date for analysis
- `end_date` (date): End date for analysis

## 🔄 Event Sourcing API

### 📚 Event History

#### Get Product Event History
```http
GET /api/v1/events/product/{product_id}/history
Authorization: Bearer {admin_token}
```

#### Get Order Event History
```http
GET /api/v1/events/order/{order_id}/history
Authorization: Bearer {token}
```

#### Get Event Statistics
```http
GET /api/v1/events/statistics
Authorization: Bearer {admin_token}
```

## 🚨 Error Handling

### Standard Error Response
```json
{
  "detail": "Error description",
  "error_code": "SPECIFIC_ERROR_CODE",
  "timestamp": "2024-12-22T10:30:00Z"
}
```

### Common HTTP Status Codes
- **200**: Success
- **201**: Created
- **400**: Bad Request
- **401**: Unauthorized
- **403**: Forbidden
- **404**: Not Found
- **422**: Validation Error
- **429**: Rate Limited
- **500**: Internal Server Error

### Validation Errors
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## 📚 SDK and Client Libraries

### Python Client Example
```python
import httpx

class Brain2GainClient:
    def __init__(self, base_url: str, token: str = None):
        self.base_url = base_url
        self.token = token
        self.client = httpx.Client()
    
    def get_products(self, skip: int = 0, limit: int = 50):
        response = self.client.get(
            f"{self.base_url}/api/v1/products",
            params={"skip": skip, "limit": limit}
        )
        return response.json()
    
    def add_to_cart(self, product_id: str, quantity: int):
        response = self.client.post(
            f"{self.base_url}/api/v1/cart/items",
            headers={"Authorization": f"Bearer {self.token}"},
            json={"product_id": product_id, "quantity": quantity}
        )
        return response.json()

# Usage
client = Brain2GainClient("http://localhost:8000", "your_token")
products = client.get_products()
```

### JavaScript/TypeScript Client
```typescript
// Auto-generated client available at frontend/src/client/
import { ApiClient } from './client';

const client = new ApiClient({
  baseUrl: 'http://localhost:8000',
  token: 'your_token'
});

// Get products
const products = await client.products.getProducts();

// Add to cart
await client.cart.addItem({
  product_id: 'product_uuid',
  quantity: 2
});
```

## 🔧 Rate Limiting

### Limits
- **Anonymous users**: 20 requests/minute
- **Authenticated users**: 200 requests/minute
- **Admin users**: 500 requests/minute

### Headers
```http
X-RateLimit-Limit: 200
X-RateLimit-Remaining: 199
X-RateLimit-Reset: 1640995200
```

## 🧪 Testing

### API Testing
```bash
# Test authentication
curl -X POST "http://localhost:8000/api/v1/login/access-token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=test@example.com&password=testpass"

# Test protected endpoint
curl -X GET "http://localhost:8000/api/v1/users/me" \
     -H "Authorization: Bearer YOUR_TOKEN"
```

### Health Check
```http
GET /health
```
**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-12-22T10:30:00Z",
  "version": "1.0.0",
  "database": "connected",
  "cache": "connected"
}
```

## 📋 Changelog

### Version 1.0.0 (Phase 1 MVP)
- ✅ Complete e-commerce API
- ✅ Order management system
- ✅ Payment processing
- ✅ Event sourcing
- ✅ Authentication and authorization
- ✅ Rate limiting
- ✅ Comprehensive error handling

---

For more information, visit the [interactive API documentation](http://localhost:8000/docs) when running the development server.