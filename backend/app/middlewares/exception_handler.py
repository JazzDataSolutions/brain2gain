"""
Exception handling middleware for Brain2Gain API.

Provides centralized error handling, logging, and consistent error responses.
"""

import logging
import traceback
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

logger = logging.getLogger(__name__)


class ExceptionHandlerMiddleware:
    """Centralized exception handling middleware."""

    def __init__(self, app: FastAPI):
        self.app = app
        self._register_handlers()

    def _register_handlers(self):
        """Register all exception handlers."""
        self.app.add_exception_handler(HTTPException, self._http_exception_handler)
        self.app.add_exception_handler(
            RequestValidationError, self._validation_exception_handler
        )
        self.app.add_exception_handler(
            ValidationError, self._pydantic_validation_handler
        )
        self.app.add_exception_handler(ValueError, self._value_error_handler)
        self.app.add_exception_handler(IntegrityError, self._integrity_error_handler)
        self.app.add_exception_handler(SQLAlchemyError, self._database_error_handler)
        self.app.add_exception_handler(Exception, self._unhandled_exception_handler)

    async def _http_exception_handler(
        self, request: Request, exc: HTTPException
    ) -> JSONResponse:
        """Handle HTTP exceptions."""
        error_id = str(uuid.uuid4())

        logger.warning(
            f"HTTP Exception {exc.status_code}: {exc.detail}",
            extra={
                "error_id": error_id,
                "status_code": exc.status_code,
                "detail": exc.detail,
                "url": str(request.url),
                "method": request.method,
            },
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "error_id": error_id, "type": "http_error"},
        )

    async def _validation_exception_handler(
        self, request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handle request validation errors."""
        error_id = str(uuid.uuid4())

        # Format validation errors for better UX
        formatted_errors = []
        for error in exc.errors():
            field_path = " -> ".join(str(loc) for loc in error["loc"])
            formatted_errors.append(
                {"field": field_path, "message": error["msg"], "type": error["type"]}
            )

        logger.warning(
            f"Validation error on {request.method} {request.url}",
            extra={
                "error_id": error_id,
                "errors": formatted_errors,
                "url": str(request.url),
                "method": request.method,
            },
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Validation error",
                "errors": formatted_errors,
                "error_id": error_id,
                "type": "validation_error",
            },
        )

    async def _pydantic_validation_handler(
        self, request: Request, exc: ValidationError
    ) -> JSONResponse:
        """Handle Pydantic validation errors."""
        error_id = str(uuid.uuid4())

        logger.warning(
            f"Pydantic validation error: {str(exc)}",
            extra={
                "error_id": error_id,
                "url": str(request.url),
                "method": request.method,
            },
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Data validation error",
                "errors": exc.errors(),
                "error_id": error_id,
                "type": "pydantic_validation_error",
            },
        )

    async def _value_error_handler(
        self, request: Request, exc: ValueError
    ) -> JSONResponse:
        """Handle business logic validation errors."""
        error_id = str(uuid.uuid4())

        logger.warning(
            f"Business validation error: {str(exc)}",
            extra={
                "error_id": error_id,
                "url": str(request.url),
                "method": request.method,
            },
        )

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "detail": str(exc),
                "error_id": error_id,
                "type": "business_validation_error",
            },
        )

    async def _integrity_error_handler(
        self, request: Request, exc: IntegrityError
    ) -> JSONResponse:
        """Handle database integrity constraint violations."""
        error_id = str(uuid.uuid4())

        # Parse common integrity errors
        error_message = "Database constraint violation"
        if "UNIQUE constraint failed" in str(exc.orig):
            error_message = "Resource already exists"
        elif "FOREIGN KEY constraint failed" in str(exc.orig):
            error_message = "Referenced resource not found"
        elif "NOT NULL constraint failed" in str(exc.orig):
            error_message = "Required field is missing"

        logger.error(
            f"Database integrity error: {str(exc)}",
            extra={
                "error_id": error_id,
                "url": str(request.url),
                "method": request.method,
            },
        )

        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "detail": error_message,
                "error_id": error_id,
                "type": "integrity_error",
            },
        )

    async def _database_error_handler(
        self, request: Request, exc: SQLAlchemyError
    ) -> JSONResponse:
        """Handle general database errors."""
        error_id = str(uuid.uuid4())

        logger.error(
            f"Database error: {str(exc)}",
            extra={
                "error_id": error_id,
                "url": str(request.url),
                "method": request.method,
                "traceback": traceback.format_exc(),
            },
        )

        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "detail": "Database service temporarily unavailable",
                "error_id": error_id,
                "type": "database_error",
            },
        )

    async def _unhandled_exception_handler(
        self, request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle unexpected exceptions."""
        error_id = str(uuid.uuid4())

        logger.error(
            f"Unhandled exception: {type(exc).__name__}: {str(exc)}",
            extra={
                "error_id": error_id,
                "exception_type": type(exc).__name__,
                "url": str(request.url),
                "method": request.method,
                "traceback": traceback.format_exc(),
            },
        )

        # Don't expose internal error details in production
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "An unexpected error occurred",
                "error_id": error_id,
                "type": "internal_server_error",
            },
        )


def setup_exception_handlers(app: FastAPI) -> None:
    """Setup exception handlers for the FastAPI app."""
    ExceptionHandlerMiddleware(app)


# Custom exception classes for business logic
class BusinessValidationError(ValueError):
    """Raised when business validation fails."""

    pass


class ResourceNotFoundError(Exception):
    """Raised when a requested resource is not found."""

    def __init__(self, resource_type: str, resource_id: Any):
        self.resource_type = resource_type
        self.resource_id = resource_id
        super().__init__(f"{resource_type} with ID {resource_id} not found")


class ResourceConflictError(Exception):
    """Raised when a resource conflict occurs."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class InsufficientPermissionsError(Exception):
    """Raised when user lacks required permissions."""

    def __init__(self, required_permission: str):
        self.required_permission = required_permission
        super().__init__(f"Insufficient permissions: {required_permission} required")
