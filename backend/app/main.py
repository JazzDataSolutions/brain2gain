from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.products import router as products_router
from app.api.dependencies import get_product_service
from app.dashboard.app import dash_app
from starlette.middleware.wsgi import WSGIMiddleware
from app.middlewares import error_handler

def create_app() -> FastAPI:
    app = FastAPI(title="Brain2Gain ERP")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(
        products_router,
        prefix="/api/v1/products",
        dependencies=[Depends(get_product_service)]
    )

    app.mount("/dash", WSGIMiddleware(dash_app.server))
    return app

app = create_app()
app.include_router(products_router, prefix="/api/v1")
error_handler.init(app)

