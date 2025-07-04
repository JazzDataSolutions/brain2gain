#!/usr/bin/env python3
"""
Complete backend startup script that bypasses problematic Alembic migrations.
Creates database tables directly and starts the full FastAPI application.
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

def test_redis_connection():
    """Test Redis connection with the corrected URL."""
    try:
        from app.core.cache import get_redis_client
        import asyncio
        
        async def test_redis():
            client = await get_redis_client()
            await client.ping()
            return True
            
        result = asyncio.run(test_redis())
        print("✅ Redis connection successful")
        return True
        
    except Exception as e:
        print(f"⚠️ Redis connection failed: {e}")
        print("🔄 Continuing with memory fallback...")
        return False

def test_rate_limiting():
    """Test rate limiting configuration."""
    try:
        from app.middlewares.advanced_rate_limiting import _get_storage_uri
        from app.core.config import settings
        
        storage_uri = _get_storage_uri()
        print(f"📊 Rate limiting storage: {storage_uri}")
        
        if storage_uri.startswith("redis://"):
            print("✅ Rate limiting configured with Redis")
        else:
            print("⚠️ Rate limiting using memory fallback")
            
        return True
        
    except Exception as e:
        print(f"❌ Rate limiting test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Brain2Gain Complete Backend...")
    
    # Create database tables
    if not create_tables():
        print("❌ Failed to create database tables")
        sys.exit(1)
    
    # Test Redis connection
    test_redis_connection()
    
    # Test rate limiting
    test_rate_limiting()
    
    print("🌐 Starting FastAPI application...")
    
    # Start the complete FastAPI application
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        workers=1,
        log_level="info",
        access_log=True,
        reload=False
    )