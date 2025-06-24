"""
Brain2Gain FastAPI Application.

Main application setup with middleware, exception handling, and API routes.
"""

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime

try:
    import sentry_sdk
except ImportError:  # pragma: no cover – optional dependency
    sentry_sdk = None  # type: ignore

from alembic import command as alembic_command
from alembic.config import Config as AlembicConfig
from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.core.cache import close_redis, get_cache_health, init_redis
from app.core.config import settings
from app.middlewares.advanced_rate_limiting import setup_rate_limiting
from app.middlewares.exception_handler import setup_exception_handlers

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Get application mode from environment
APP_MODE = os.getenv("APP_MODE", "production")
API_MODE = os.getenv("API_MODE", "full")


def custom_generate_unique_id(route: APIRoute) -> str:
    """Generate unique IDs for API routes."""
    tag = route.tags[0] if route.tags else "default"
    return f"{tag}-{route.name}"


def run_migrations() -> None:
    """Run database migrations on startup."""
    try:
        project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
        )
        ini_path = os.path.join(project_root, "alembic.ini")
        cfg = AlembicConfig(ini_path)
        cfg.set_main_option("script_location", "app/alembic")
        alembic_command.upgrade(cfg, "head")
        logger.info("Database migrations completed successfully")
    except Exception as e:
        logger.error(f"Failed to run migrations: {e}")
        # Don't fail startup if migrations fail in development
        if settings.ENVIRONMENT == "production":
            raise


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    logger.info("Starting Brain2Gain API...")

    # Initialize database migrations
    run_migrations()

    # Initialize Redis cache
    try:
        await init_redis()
        logger.info("Redis cache initialized successfully")
    except Exception as e:
        logger.warning(f"Redis initialization failed: {e}")
        logger.info("Continuing without Redis cache (using mock)")

    logger.info("Brain2Gain API started successfully")

    yield

    # Shutdown
    logger.info("Shutting down Brain2Gain API...")

    # Close Redis connection
    try:
        await close_redis()
        logger.info("Redis connection closed")
    except Exception as e:
        logger.error(f"Error closing Redis connection: {e}")

    logger.info("Brain2Gain API shutdown complete")


# Initialize Sentry for error tracking
if sentry_sdk and settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(
        dsn=str(settings.SENTRY_DSN),
        enable_tracing=True,
        environment=settings.ENVIRONMENT,
    )
    logger.info("Sentry error tracking initialized")

# Create FastAPI application with mode-specific configuration
app_title = settings.PROJECT_NAME
app_description = "Brain2Gain E-commerce API for sports supplements"

if API_MODE == "public" or API_MODE == "store":
    app_title = "Brain2Gain Store API"
    app_description = "Public API for Brain2Gain e-commerce store"
elif API_MODE == "admin":
    app_title = "Brain2Gain Admin API"
    app_description = "Administrative API for Brain2Gain ERP system"

app = FastAPI(
    title=app_title,
    description=app_description,
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json" if API_MODE != "public" else None,
    generate_unique_id_function=custom_generate_unique_id,
    lifespan=lifespan,
)

# Setup exception handlers
setup_exception_handlers(app)

# Setup advanced rate limiting
setup_rate_limiting(app)

# Configure CORS based on API mode
cors_origins = []

if API_MODE == "public" or API_MODE == "store":
    # Store/Public API CORS
    cors_origins = ["http://localhost:3000"]  # Store frontend
    if settings.ENVIRONMENT == "production":
        cors_origins.extend(
            [
                "https://store.brain2gain.com",
                "https://www.brain2gain.com",
                "https://brain2gain.com",
            ]
        )
    elif settings.ENVIRONMENT == "development":
        cors_origins.extend(["http://localhost:3000", "http://127.0.0.1:3000"])
elif API_MODE == "admin":
    # Admin API CORS
    cors_origins = ["http://localhost:3001"]  # Admin frontend
    if settings.ENVIRONMENT == "production":
        cors_origins.extend(["https://admin.brain2gain.com"])
    elif settings.ENVIRONMENT == "development":
        cors_origins.extend(["http://localhost:3001", "http://127.0.0.1:3001"])
else:
    # Full mode (backward compatibility)
    cors_origins = ["http://localhost:5173"]
    if settings.ENVIRONMENT == "production":
        cors_origins.extend(
            [
                "https://brain2gain.com",
                "https://www.brain2gain.com",
                "https://frontend.brain2gain.com",
            ]
        )
    elif settings.ENVIRONMENT == "development":
        cors_origins.extend(
            [
                "http://localhost:3000",
                "http://localhost:3001",
                "http://localhost:5173",
                "http://127.0.0.1:5173",
            ]
        )

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
        "Origin",
        "User-Agent",
        "DNT",
        "Cache-Control",
        "X-Mx-ReqToken",
        "Keep-Alive",
        "X-Requested-With",
        "If-Modified-Since",
    ],
    max_age=86400,  # 24 hours
)

# Include API routes
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint.

    Returns overall system health including cache status,
    useful for load balancers and monitoring systems.
    """
    # Get cache health status
    cache_health = await get_cache_health()

    # Determine overall health status
    overall_status = "healthy"
    if cache_health.get("health") == "critical":
        overall_status = "degraded"  # Service works but cache is down
    elif not cache_health.get("connected", False):
        overall_status = "degraded"

    # Build comprehensive health response
    health_response = {
        "status": overall_status,
        "service": "Brain2Gain API",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "components": {
            "api": {
                "status": "healthy",
                "description": "FastAPI application is running",
            },
            "cache": {
                "status": cache_health.get("status", "unknown"),
                "health": cache_health.get("health", "unknown"),
                "connected": cache_health.get("connected", False),
                "hit_rate": cache_health.get("hit_rate", 0),
                "type": cache_health.get("cache_type", "unknown"),
            },
        },
        "checks": {
            "cache_connectivity": cache_health.get("connected", False),
            "cache_performance": cache_health.get("hit_rate", 0) >= 60,
            "api_responsive": True,
        },
    }

    # Add error details if cache is unhealthy
    if cache_health.get("error"):
        health_response["components"]["cache"]["error"] = cache_health["error"]

    return health_response


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to Brain2Gain API",
        "docs": f"{settings.API_V1_STR}/docs",
        "health": "/health",
        "version": "1.0.0",
    }
