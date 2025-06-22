import os

from fastapi import APIRouter

from app.api.routes import (
    analytics,
    cart,
    events,
    items,
    login,
    orders,
    payments,
    private,
    users,
    utils,
    websocket,
)
from app.api.v1 import products
from app.core.config import settings

# Get API mode from environment
API_MODE = os.getenv("API_MODE", "full")
ENABLE_ADMIN_ROUTES = os.getenv("ENABLE_ADMIN_ROUTES", "true").lower() == "true"
ENABLE_STORE_ROUTES = os.getenv("ENABLE_STORE_ROUTES", "true").lower() == "true"

api_router = APIRouter()

# Always include basic utils
api_router.include_router(utils.router)

# Store/Public routes
if API_MODE in ["public", "store", "full"] and ENABLE_STORE_ROUTES:
    api_router.include_router(products.router)  # Product catalog
    api_router.include_router(cart.router)      # Shopping cart
    api_router.include_router(orders.router, prefix="/orders", tags=["orders"])  # Order management
    api_router.include_router(payments.router, prefix="/payments", tags=["payments"])  # Payment processing
    api_router.include_router(login.router)     # Basic auth for customers

# Admin routes
if API_MODE in ["admin", "full"] and ENABLE_ADMIN_ROUTES:
    api_router.include_router(users.router)     # User management
    api_router.include_router(items.router)     # Admin item management
    api_router.include_router(login.router)     # Admin authentication
    api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])  # Analytics
    api_router.include_router(events.router, prefix="/events", tags=["events"])  # Event Sourcing

    # Debug routes only for local admin
    if settings.ENVIRONMENT == "local":
        api_router.include_router(private.router)

# WebSocket routes (available in all modes)
api_router.include_router(websocket.router, prefix="/ws", tags=["websocket"])
