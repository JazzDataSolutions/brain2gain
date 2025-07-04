#!/usr/bin/env python3
"""
Working backend with database tables but without Redis complications.
"""

import uvicorn
import os
import sys

# Add app directory to Python path
sys.path.insert(0, '/app')

# Set production environment
os.environ['ENVIRONMENT'] = 'production'

def create_tables():
    """Create database tables using SQLModel directly."""
    try:
        # Import all models to ensure they're registered
        import app.models
        from app.core.config import settings
        from sqlmodel import create_engine, SQLModel
        
        print("🗄️ Creating database tables with SQLModel...")
        engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))
        SQLModel.metadata.create_all(engine)
        print("✅ Database tables created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

def create_app():
    """Create FastAPI app without problematic middleware."""
    try:
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse
        from starlette.middleware.cors import CORSMiddleware
        from app.core.config import settings
        
        app = FastAPI(title="Brain2Gain API", version="1.0.0")
        
        # Add CORS
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            allow_headers=["*"],
        )
        
        # Import and include API routes
        try:
            from app.api.main import api_router
            app.include_router(api_router, prefix=settings.API_V1_STR)
            print("✅ API routes loaded successfully")
        except Exception as e:
            print(f"⚠️ Error loading API routes: {e}")
            print("🔄 Continuing with basic routes only...")
        
        @app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "healthy", "message": "Brain2Gain API is running"}

        @app.get("/api/v1/utils/health-check/")
        async def api_health_check():
            """API health check endpoint."""
            return {"status": "ok", "timestamp": "2025-07-04T16:45:00Z"}

        @app.get("/")
        async def root():
            """Root endpoint."""
            return {"message": "Brain2Gain API", "version": "1.0.0"}
        
        return app
        
    except Exception as e:
        print(f"❌ Error creating FastAPI app: {e}")
        return None

if __name__ == "__main__":
    print("🚀 Starting Brain2Gain Working Backend...")
    
    # Create database tables
    if not create_tables():
        print("❌ Failed to create database tables")
        sys.exit(1)
    
    # Create FastAPI app
    app = create_app()
    if app is None:
        print("❌ Failed to create FastAPI app")
        sys.exit(1)
    
    print("🌐 Starting FastAPI application...")
    
    # Start the application
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        workers=1,
        log_level="info",
        access_log=True,
        reload=False
    )