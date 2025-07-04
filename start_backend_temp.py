#!/usr/bin/env python3
"""
Temporary backend startup script for production deployment.
Creates database tables and starts the backend API.
"""

import uvicorn
import os
import sys

# Add app directory to Python path
sys.path.insert(0, '/app')

# Set production environment
os.environ['ENVIRONMENT'] = 'production'

def create_tables():
    """Create database tables using SQLModel."""
    try:
        # Import at module level for proper import handling
        import app.models
        from app.core.config import settings
        from sqlmodel import create_engine, SQLModel
        
        print("Creating database tables...")
        engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))
        SQLModel.metadata.create_all(engine)
        print("✅ Database tables created successfully")
        
        print("✅ Admin user setup skipped (will be created by main app)")
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        # Continue anyway, tables might already exist

if __name__ == "__main__":
    # Create tables first
    create_tables()
    
    # Start with basic configuration
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        workers=1,
        log_level="info",
        access_log=True,
        reload=False
    )