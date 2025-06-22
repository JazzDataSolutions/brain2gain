# app/middlewares/error_handler.py
from fastapi import Request
from fastapi.responses import JSONResponse


async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc)}
        )

def init(app):
    app.middleware("http")(catch_exceptions_middleware)

