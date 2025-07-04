#!/usr/bin/env python3
"""
Simple backend test to check what's working and what's not.
"""

import json
import sys
import traceback

def test_imports():
    """Test basic imports."""
    print("🧪 Testing basic imports...")
    
    try:
        import fastapi
        print(f"✅ FastAPI: {fastapi.__version__}")
    except ImportError as e:
        print(f"❌ FastAPI: {e}")
        return False
        
    try:
        import uvicorn
        print(f"✅ Uvicorn: {uvicorn.__version__}")
    except ImportError as e:
        print(f"❌ Uvicorn: {e}")
        return False
        
    return True

def test_basic_app():
    """Test basic FastAPI app creation."""
    print("\n🏗️ Testing basic FastAPI app...")
    
    try:
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse
        
        app = FastAPI(title="Test App")
        
        @app.get("/test")
        def test_endpoint():
            return {"status": "working"}
            
        print("✅ Basic FastAPI app created successfully")
        return app
        
    except Exception as e:
        print(f"❌ Failed to create basic app: {e}")
        traceback.print_exc()
        return None

def test_database_config():
    """Test database configuration."""
    print("\n🗄️ Testing database configuration...")
    
    try:
        # Import without triggering full app startup
        import os
        os.environ['ENVIRONMENT'] = 'production'
        
        from app.core.config import settings
        
        print(f"✅ Database URI: {str(settings.SQLALCHEMY_DATABASE_URI)[:50]}...")
        print(f"✅ Redis URL: {settings.REDIS_URL[:30]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Database config failed: {e}")
        traceback.print_exc()
        return False

def test_models():
    """Test model imports."""
    print("\n📊 Testing model imports...")
    
    try:
        import app.models
        print("✅ Models imported successfully")
        
        # Try to create tables
        from sqlmodel import create_engine, SQLModel
        from app.core.config import settings
        
        engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))
        SQLModel.metadata.create_all(engine)
        print("✅ Database tables created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Models/database failed: {e}")
        traceback.print_exc()
        return False

def test_api_routes():
    """Test API route imports."""
    print("\n🛣️ Testing API route imports...")
    
    route_tests = [
        ("utils", "app.api.routes.utils"),
        ("auth", "app.api.routes.auth"),
        ("users", "app.api.routes.users"),
        ("login", "app.api.routes.login"),
        ("products", "app.api.v1.products"),
        ("cart", "app.api.routes.cart"),
        ("orders", "app.api.routes.orders"),
    ]
    
    working_routes = []
    failed_routes = []
    
    for route_name, module_path in route_tests:
        try:
            module = __import__(module_path, fromlist=["router"])
            if hasattr(module, "router"):
                print(f"✅ {route_name}: router found")
                working_routes.append(route_name)
            else:
                print(f"⚠️ {route_name}: module imported but no router")
                failed_routes.append(route_name)
        except Exception as e:
            print(f"❌ {route_name}: {e}")
            failed_routes.append(route_name)
    
    return working_routes, failed_routes

def create_minimal_working_app():
    """Create a minimal working app with available routes."""
    print("\n🔧 Creating minimal working app...")
    
    try:
        from fastapi import FastAPI
        from starlette.middleware.cors import CORSMiddleware
        
        app = FastAPI(
            title="Brain2Gain API - Minimal",
            version="1.0.0",
            description="Minimal working Brain2Gain API"
        )
        
        # Add CORS
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            allow_headers=["*"],
        )
        
        # Add basic endpoints
        @app.get("/health")
        def health_check():
            return {
                "status": "healthy",
                "message": "Brain2Gain API - Minimal Working Version",
                "version": "1.0.0"
            }
        
        @app.get("/api/v1/utils/health-check/")
        def api_health_check():
            return {
                "status": "ok",
                "timestamp": "2025-07-04T17:00:00Z",
                "version": "minimal"
            }
        
        @app.get("/")
        def root():
            return {
                "message": "Brain2Gain API - Minimal",
                "docs": "/docs",
                "health": "/health"
            }
        
        # Try to add working routes
        working_routes, failed_routes = test_api_routes()
        
        for route_name in working_routes:
            try:
                if route_name == "utils":
                    from app.api.routes.utils import router
                    app.include_router(router)
                elif route_name == "auth":
                    from app.api.routes.auth import router
                    app.include_router(router, prefix="/auth", tags=["auth"])
                elif route_name == "products":
                    from app.api.v1.products import router
                    app.include_router(router)
                elif route_name == "users":
                    from app.api.routes.users import router
                    app.include_router(router, prefix="/users", tags=["users"])
                elif route_name == "login":
                    from app.api.routes.login import router
                    app.include_router(router)
                    
                print(f"✅ Added {route_name} routes to app")
                
            except Exception as e:
                print(f"⚠️ Failed to add {route_name} routes: {e}")
        
        print(f"\n✅ Minimal app created with {len(working_routes)} route modules")
        print(f"❌ Failed routes: {failed_routes}")
        
        return app
        
    except Exception as e:
        print(f"❌ Failed to create minimal app: {e}")
        traceback.print_exc()
        return None

def main():
    """Run all tests."""
    print("🚀 Brain2Gain Backend Diagnostic Test\n")
    
    # Set environment
    import os
    os.environ['ENVIRONMENT'] = 'production'
    
    # Add paths
    sys.path.insert(0, '/app')
    sys.path.insert(0, '/app/backend')
    
    # Run tests
    if not test_imports():
        print("\n❌ Basic imports failed. Cannot continue.")
        return
    
    if not test_database_config():
        print("\n❌ Database configuration failed.")
        return
        
    if not test_models():
        print("\n❌ Database/models failed.")
        return
    
    # Test and create minimal app
    app = create_minimal_working_app()
    
    if app is None:
        print("\n❌ Failed to create any working app.")
        return
    
    # Start the app
    print("\n🌐 Starting minimal working API server...")
    
    try:
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")

if __name__ == "__main__":
    main()