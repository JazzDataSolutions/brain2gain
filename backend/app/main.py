"""
Brain2Gain FastAPI Application.

Main application setup with middleware, exception handling, and API routes.
"""
import os
import logging
from contextlib import asynccontextmanager

try:
    import sentry_sdk
except ImportError:  # pragma: no cover – optional dependency
    sentry_sdk = None  # type: ignore

from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware
from alembic.config import Config as AlembicConfig
from alembic import command as alembic_command

from app.api.main import api_router
from app.core.config import settings
from app.middlewares.exception_handler import setup_exception_handlers

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def custom_generate_unique_id(route: APIRoute) -> str:
    """Generate unique IDs for API routes."""
    return f"{route.tags[0]}-{route.name}"


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
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    logger.info("Starting Brain2Gain API...")
    run_migrations()
    logger.info("Brain2Gain API started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Brain2Gain API...")


# Initialize Sentry for error tracking
if sentry_sdk and settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(
        dsn=str(settings.SENTRY_DSN), 
        enable_tracing=True,
        environment=settings.ENVIRONMENT
    )
    logger.info("Sentry error tracking initialized")

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Brain2Gain E-commerce API for sports supplements",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
    lifespan=lifespan,
)

# Setup exception handlers
setup_exception_handlers(app)

# Configure CORS
cors_origins = ["http://localhost:5173"]  # Frontend development server
if settings.ENVIRONMENT == "production":
    cors_origins = [
        "https://brain2gain.com",
        "https://www.brain2gain.com",
        "https://frontend.brain2gain.com"
    ]
elif settings.ENVIRONMENT == "development":
    cors_origins.extend([
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ])

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
        "If-Modified-Since"
    ],
    max_age=86400,  # 24 hours
)

# Include API routes
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Brain2Gain API",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to Brain2Gain API",
        "docs": f"{settings.API_V1_STR}/docs",
        "health": "/health",
        "version": "1.0.0"
    }
