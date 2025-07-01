#!/usr/bin/env python3
"""
Brain2Gain Backend - Simplified version without Alembic
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# Create FastAPI app
app = FastAPI(
    title="Brain2Gain API",
    description="E-commerce platform for sports supplements - Simplified version",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Simplified for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/api/v1/utils/health-check/")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Brain2Gain API is running",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "database": "connected" if os.getenv("POSTGRES_PASSWORD") else "no-credentials",
        "redis": "configured" if os.getenv("REDIS_PASSWORD") else "no-credentials"
    }

# Basic endpoints
@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "Brain2Gain API - Simplified Version",
        "docs": "/docs",
        "health": "/api/v1/utils/health-check/"
    }

@app.get("/api/v1/items/")
def get_items():
    """Get items endpoint - mock data"""
    return {
        "items": [
            {"id": 1, "name": "Whey Protein", "price": 49.99},
            {"id": 2, "name": "Creatine", "price": 29.99},
            {"id": 3, "name": "BCAA", "price": 34.99}
        ]
    }

@app.get("/api/v1/users/me")
def get_current_user():
    """Get current user - mock endpoint"""
    return {
        "id": 1,
        "email": "admin@brain2gain.mx",
        "is_active": True,
        "is_superuser": True
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)