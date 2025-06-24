"""
Advanced Rate Limiting with Redis for Brain2Gain API.

Implements the rate limiting strategy from IMMEDIATE_IMPROVEMENTS.md
with SlowAPI and Redis for distributed rate limiting.
"""

import logging

from fastapi import HTTPException, Request, status
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.core.cache import get_redis_client
from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize limiter with Redis storage
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.REDIS_URL,
    default_limits=["200/minute", "2000/hour", "10000/day"],
    strategy="moving-window",
)


def get_rate_limit_key(request: Request) -> str:
    """
    Generate rate limit key based on user authentication and role.

    This function determines the appropriate rate limiting based on:
    - User authentication status
    - User role (admin, user, anonymous)
    - IP address for anonymous users
    """
    # Check for authenticated user in request state
    user = getattr(request.state, "user", None)

    if user:
        # Authenticated user - use user ID and role
        if hasattr(user, "role") and user.role == "admin":
            return f"admin:{user.id}"
        elif hasattr(user, "is_superuser") and user.is_superuser:
            return f"admin:{user.id}"
        else:
            return f"user:{user.id}"

    # Anonymous user - use IP address
    return get_remote_address(request)


def get_user_role_from_request(request: Request) -> str:
    """Determine user role from request for rate limiting."""
    user = getattr(request.state, "user", None)

    if user:
        if hasattr(user, "role") and user.role == "admin":
            return "admin"
        elif hasattr(user, "is_superuser") and user.is_superuser:
            return "admin"
        else:
            return "user"

    return "anonymous"


# Rate limiting decorators for different user types
def apply_endpoint_limits(endpoint_type: str = "default"):
    """
    Apply rate limits based on endpoint type and user role.

    Args:
        endpoint_type: Type of endpoint (auth, products, orders, etc.)
    """
    limits = {
        "auth": "5/minute",  # Login attempts - strict
        "products": "100/minute",  # Product browsing - generous
        "orders": "10/hour",  # Order creation - prevent spam
        "cart": "50/minute",  # Cart operations - moderate
        "default": "60/minute",  # Default limit
    }

    limit_str = limits.get(endpoint_type, limits["default"])

    def rate_limit_key_func(request: Request):
        return get_rate_limit_key(request)

    return limiter.limit(limit_str, key_func=rate_limit_key_func)


# Custom rate limit exceeded handler
async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """
    Custom handler for rate limit exceeded responses.

    Provides detailed information about the rate limit and retry timing.
    """
    user_role = get_user_role_from_request(request)

    logger.warning(
        "Rate limit exceeded",
        extra={
            "user_role": user_role,
            "client_ip": get_remote_address(request),
            "path": request.url.path,
            "method": request.method,
            "limit": str(exc.detail),
            "retry_after": exc.retry_after,
        },
    )

    # Calculate retry after seconds
    retry_after = exc.retry_after if exc.retry_after else 60

    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail={
            "error": "Rate limit exceeded",
            "message": f"Too many requests for {user_role} user",
            "retry_after": retry_after,
            "limit": str(exc.detail),
            "user_type": user_role,
            "recommendation": _get_rate_limit_recommendation(user_role),
        },
        headers={"Retry-After": str(retry_after), "X-RateLimit-Scope": user_role},
    )


def _get_rate_limit_recommendation(user_role: str) -> str:
    """Provide recommendations based on user role."""
    recommendations = {
        "anonymous": "Consider creating an account for higher rate limits",
        "user": "Your rate limit will reset soon. For unlimited access, contact support",
        "admin": "Admin rate limit exceeded - this may indicate an issue",
    }
    return recommendations.get(user_role, "Please wait before making more requests")


# Rate limiting metrics tracking
class RateLimitMetrics:
    """Track rate limiting metrics for monitoring."""

    def __init__(self):
        self.blocked_requests = 0
        self.total_requests = 0
        self.blocked_by_role = {"anonymous": 0, "user": 0, "admin": 0}

    def record_request(self, user_role: str, blocked: bool = False):
        """Record a request for metrics."""
        self.total_requests += 1
        if blocked:
            self.blocked_requests += 1
            self.blocked_by_role[user_role] += 1

    def get_stats(self) -> dict:
        """Get rate limiting statistics."""
        block_rate = (
            (self.blocked_requests / self.total_requests * 100)
            if self.total_requests > 0
            else 0
        )

        return {
            "total_requests": self.total_requests,
            "blocked_requests": self.blocked_requests,
            "block_rate_percentage": round(block_rate, 2),
            "blocked_by_role": self.blocked_by_role.copy(),
            "status": (
                "healthy"
                if block_rate < 5
                else "warning" if block_rate < 15 else "critical"
            ),
        }

    def reset(self):
        """Reset metrics counters."""
        self.blocked_requests = 0
        self.total_requests = 0
        self.blocked_by_role = {"anonymous": 0, "user": 0, "admin": 0}


# Global metrics instance
rate_limit_metrics = RateLimitMetrics()


async def get_rate_limit_stats() -> dict:
    """Get comprehensive rate limiting statistics."""
    try:
        redis_client = await get_redis_client()

        # Get Redis rate limiting stats if available
        redis_stats = {}
        if hasattr(redis_client, "info"):
            try:
                info = await redis_client.info()
                redis_stats = {
                    "commands_processed": info.get("total_commands_processed", 0),
                    "connected_clients": info.get("connected_clients", 0),
                }
            except Exception as e:
                logger.warning(f"Could not get Redis stats: {e}")

        # Combine with application metrics
        app_stats = rate_limit_metrics.get_stats()

        return {
            "rate_limiting": app_stats,
            "redis": redis_stats,
            "configuration": {
                "anonymous_limit": settings.RATE_LIMIT_ANONYMOUS,
                "authenticated_limit": settings.RATE_LIMIT_AUTHENTICATED,
                "period_seconds": settings.RATE_LIMIT_PERIOD,
                "storage": "redis" if redis_stats else "memory",
            },
            "health": {
                "status": app_stats["status"],
                "recommendation": _get_system_recommendation(
                    app_stats["block_rate_percentage"]
                ),
            },
        }

    except Exception as e:
        logger.error(f"Error getting rate limit stats: {e}")
        return {"error": str(e), "rate_limiting": rate_limit_metrics.get_stats()}


def _get_system_recommendation(block_rate: float) -> str:
    """Get system recommendations based on block rate."""
    if block_rate < 1:
        return "Rate limiting working optimally"
    elif block_rate < 5:
        return "Normal operation with occasional blocks"
    elif block_rate < 15:
        return "Consider reviewing rate limits - higher than expected block rate"
    else:
        return "High block rate detected - investigate potential abuse or adjust limits"


# Setup function for FastAPI app
def setup_rate_limiting(app):
    """
    Setup rate limiting for FastAPI application.

    Args:
        app: FastAPI application instance
    """
    # Add SlowAPI middleware
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)
    app.add_middleware(SlowAPIMiddleware)

    logger.info("Advanced rate limiting with Redis initialized")


# Export main components
__all__ = [
    "limiter",
    "get_rate_limit_key",
    "apply_endpoint_limits",
    "setup_rate_limiting",
    "get_rate_limit_stats",
    "rate_limit_metrics",
]
