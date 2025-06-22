from fastapi import APIRouter, Depends
from pydantic.networks import EmailStr

from app.api.deps import get_current_active_superuser
from app.core.cache import get_cache_health, get_cache_stats, reset_cache_metrics
from app.middlewares.advanced_rate_limiting import get_rate_limit_stats
from app.models import Message
from app.utils import generate_test_email, send_email

router = APIRouter(prefix="/utils", tags=["utils"])


@router.post(
    "/test-email/",
    dependencies=[Depends(get_current_active_superuser)],
    status_code=201,
)
def test_email(email_to: EmailStr) -> Message:
    """
    Test emails.
    """
    email_data = generate_test_email(email_to=email_to)
    send_email(
        email_to=email_to,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )
    return Message(message="Test email sent")


@router.get("/health-check/")
async def health_check() -> bool:
    return True


@router.get("/cache/stats/")
async def get_cache_statistics():
    """
    Get comprehensive cache statistics and performance metrics.
    
    Returns detailed information about cache performance, hit rates,
    memory usage, and optimization recommendations.
    """
    return await get_cache_stats()


@router.get("/cache/health/")
async def get_cache_health_status():
    """
    Get cache health status for monitoring.
    
    Returns simplified health status suitable for monitoring
    systems and alerting.
    """
    return await get_cache_health()


@router.post(
    "/cache/reset-metrics/",
    dependencies=[Depends(get_current_active_superuser)],
)
async def reset_cache_statistics():
    """
    Reset cache metrics counters.
    
    Useful for testing or starting fresh monitoring periods.
    Requires superuser permissions.
    """
    return await reset_cache_metrics()


@router.get("/rate-limiting/stats/")
async def get_rate_limiting_statistics():
    """
    Get rate limiting statistics and performance metrics.
    
    Returns information about blocked requests, user types,
    and rate limiting configuration.
    """
    return await get_rate_limit_stats()
