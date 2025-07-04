#!/usr/bin/env python3
"""
Simple backend test to verify the API works.
"""

import uvicorn
import os
import sys

# Add app directory to Python path
sys.path.insert(0, '/app')

# Set production environment
os.environ['ENVIRONMENT'] = 'production'

if __name__ == "__main__":
    # Start with minimal configuration
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        workers=1,
        log_level="info",
        access_log=True,
        reload=False
    )