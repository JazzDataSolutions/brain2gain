#!/usr/bin/env python3
"""
Minimal backend for testing production deployment.
Bypasses all problematic imports and starts a basic FastAPI server.
"""

import uvicorn
import os
import sys
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Add app directory to Python path
sys.path.insert(0, '/app')

# Set production environment
os.environ['ENVIRONMENT'] = 'production'

# Create minimal FastAPI app
app = FastAPI(title="Brain2Gain API", version="1.0.0")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "Brain2Gain API is running"}

@app.get("/api/v1/utils/health-check/")
async def api_health_check():
    """API health check endpoint."""
    return {"status": "ok", "timestamp": "2025-07-03T17:30:00Z"}

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Brain2Gain API", "version": "1.0.0"}

if __name__ == "__main__":
    # Start with basic configuration
    uvicorn.run(
        app,
        host="0.0.0.0", 
        port=8000,
        workers=1,
        log_level="info",
        access_log=True,
        reload=False
    )