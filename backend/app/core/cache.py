"""
Cache service using Redis for high-performance data caching.
Implements the cache strategy from IMMEDIATE_IMPROVEMENTS.md
"""

import json
import logging
from functools import wraps
from typing import Any, Callable, Optional, TypeVar, Union

import redis.asyncio as redis
from redis.asyncio import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)

# Redis client instance
redis_client: Optional[Redis] = None

# Type variable for generic function typing
F = TypeVar('F', bound=Callable[..., Any])

# Cache metrics tracking
cache_metrics = {
    "hits": 0,
    "misses": 0,
    "errors": 0,
    "total_requests": 0,
    "cache_size": 0
}


async def init_redis() -> Redis:
    """Initialize Redis connection."""
    global redis_client
    
    if redis_client is None:
        try:
            redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                encoding='utf-8',
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            await redis_client.ping()
            logger.info("Redis connection established successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            # Create a mock client for development without Redis
            redis_client = MockRedisClient()
            
    return redis_client


async def close_redis():
    """Close Redis connection."""
    global redis_client
    if redis_client and not isinstance(redis_client, MockRedisClient):
        await redis_client.close()
        redis_client = None


class MockRedisClient:
    """Mock Redis client for development/testing without Redis."""
    
    def __init__(self):
        self._data = {}
    
    async def get(self, key: str) -> Optional[str]:
        return self._data.get(key)
    
    async def setex(self, key: str, ttl: int, value: str) -> bool:
        self._data[key] = value
        return True
    
    async def delete(self, *keys: str) -> int:
        deleted = 0
        for key in keys:
            if key in self._data:
                del self._data[key]
                deleted += 1
        return deleted
    
    async def ping(self) -> bool:
        return True
    
    async def close(self):
        pass
    
    def scan_iter(self, match: str):
        """Mock scan_iter for pattern matching."""
        for key in self._data.keys():
            if match.replace('*', '') in key:
                yield key


async def get_redis_client() -> Redis:
    """Get Redis client instance."""
    if redis_client is None:
        return await init_redis()
    return redis_client


def cache_key_wrapper(prefix: str, ttl: int = 300):
    """
    Decorator to cache function results in Redis.
    
    Args:
        prefix: Cache key prefix
        ttl: Time to live in seconds (default: 5 minutes)
    
    Usage:
        @cache_key_wrapper("products:list", ttl=300)
        async def get_products():
            return await fetch_products()
    """
    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            client = await get_redis_client()
            
            # Generate unique cache key based on function args
            cache_key = _generate_cache_key(prefix, args, kwargs)
            
            try:
                cache_metrics["total_requests"] += 1
                
                # Try to get cached result
                cached_value = await client.get(cache_key)
                if cached_value:
                    cache_metrics["hits"] += 1
                    logger.debug(f"Cache HIT for key: {cache_key}")
                    return json.loads(cached_value)
                
                cache_metrics["misses"] += 1
                logger.debug(f"Cache MISS for key: {cache_key}")
                
                # Execute function and cache result
                result = await func(*args, **kwargs)
                
                # Cache the result (handle serialization)
                await client.setex(
                    cache_key, 
                    ttl, 
                    json.dumps(result, default=str)
                )
                
                return result
                
            except Exception as e:
                cache_metrics["errors"] += 1
                logger.error(f"Cache error for key {cache_key}: {e}")
                # If cache fails, execute function normally
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def _generate_cache_key(prefix: str, args: tuple, kwargs: dict) -> str:
    """Generate unique cache key from function arguments."""
    # Convert args to strings
    args_str = ':'.join(str(arg) for arg in args if arg is not None)
    
    # Convert kwargs to sorted key-value pairs
    kwargs_str = ':'.join(
        f"{k}={v}" for k, v in sorted(kwargs.items()) 
        if v is not None
    )
    
    # Combine all parts
    key_parts = [prefix]
    if args_str:
        key_parts.append(args_str)
    if kwargs_str:
        key_parts.append(kwargs_str)
    
    return ':'.join(key_parts)


async def invalidate_cache_pattern(pattern: str) -> int:
    """
    Invalidate all cache keys matching a pattern.
    
    Args:
        pattern: Redis key pattern (e.g., "products:*")
    
    Returns:
        Number of keys deleted
    """
    client = await get_redis_client()
    deleted_count = 0
    
    try:
        async for key in client.scan_iter(match=pattern):
            await client.delete(key)
            deleted_count += 1
        
        logger.info(f"Invalidated {deleted_count} cache keys matching pattern: {pattern}")
        return deleted_count
        
    except Exception as e:
        logger.error(f"Error invalidating cache pattern {pattern}: {e}")
        return 0


async def invalidate_cache_key(key: str) -> bool:
    """
    Invalidate specific cache key.
    
    Args:
        key: Exact cache key to delete
    
    Returns:
        True if key was deleted, False otherwise
    """
    client = await get_redis_client()
    
    try:
        result = await client.delete(key)
        if result:
            logger.debug(f"Invalidated cache key: {key}")
        return bool(result)
        
    except Exception as e:
        logger.error(f"Error invalidating cache key {key}: {e}")
        return False


async def get_cache_stats() -> dict:
    """Get comprehensive cache statistics and performance metrics."""
    client = await get_redis_client()
    
    # Calculate hit rate
    total_requests = cache_metrics["total_requests"]
    hits = cache_metrics["hits"]
    hit_rate = (hits / total_requests * 100) if total_requests > 0 else 0
    
    if isinstance(client, MockRedisClient):
        cache_metrics["cache_size"] = len(client._data)
        return {
            "type": "mock",
            "connected": True,
            "keys": len(client._data),
            "hit_rate": round(hit_rate, 2),
            "metrics": cache_metrics.copy(),
            "performance": {
                "efficiency": "excellent" if hit_rate > 80 else "good" if hit_rate > 60 else "needs_improvement",
                "recommendation": _get_cache_recommendation(hit_rate)
            }
        }
    
    try:
        info = await client.info()
        db_info = info.get("db0", {})
        redis_keys = db_info.get("keys", 0) if isinstance(db_info, dict) else 0
        cache_metrics["cache_size"] = redis_keys
        
        # Redis-specific metrics
        redis_hit_rate = 0
        redis_hits = info.get("keyspace_hits", 0)
        redis_misses = info.get("keyspace_misses", 0)
        if (redis_hits + redis_misses) > 0:
            redis_hit_rate = (redis_hits / (redis_hits + redis_misses)) * 100
        
        return {
            "type": "redis",
            "connected": True,
            "keys": redis_keys,
            "memory_used": info.get("used_memory_human", "N/A"),
            "memory_peak": info.get("used_memory_peak_human", "N/A"),
            "connected_clients": info.get("connected_clients", 0),
            "total_commands": info.get("total_commands_processed", 0),
            "uptime_seconds": info.get("uptime_in_seconds", 0),
            "redis_hit_rate": round(redis_hit_rate, 2),
            "application_hit_rate": round(hit_rate, 2),
            "metrics": cache_metrics.copy(),
            "performance": {
                "efficiency": _get_cache_efficiency(hit_rate),
                "redis_efficiency": _get_cache_efficiency(redis_hit_rate),
                "recommendation": _get_cache_recommendation(hit_rate)
            },
            "redis_info": {
                "version": info.get("redis_version", "unknown"),
                "mode": info.get("redis_mode", "standalone"),
                "role": info.get("role", "master")
            }
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return {
            "type": "redis",
            "connected": False,
            "error": str(e),
            "hit_rate": round(hit_rate, 2),
            "metrics": cache_metrics.copy()
        }


def _get_cache_efficiency(hit_rate: float) -> str:
    """Determine cache efficiency based on hit rate."""
    if hit_rate >= 90:
        return "excellent"
    elif hit_rate >= 80:
        return "very_good"
    elif hit_rate >= 70:
        return "good"
    elif hit_rate >= 60:
        return "fair"
    else:
        return "needs_improvement"


def _get_cache_recommendation(hit_rate: float) -> str:
    """Provide cache optimization recommendations."""
    if hit_rate >= 90:
        return "Cache performance is excellent. Consider monitoring for TTL optimization."
    elif hit_rate >= 80:
        return "Good cache performance. Monitor frequently accessed keys for TTL tuning."
    elif hit_rate >= 70:
        return "Decent performance. Consider increasing TTL for stable data."
    elif hit_rate >= 60:
        return "Fair performance. Review caching strategy and identify cold data."
    else:
        return "Poor performance. Review cache keys, TTL settings, and consider cache warming strategies."


# Convenience functions for common cache operations
class CacheService:
    """Service class for cache operations."""
    
    @staticmethod
    async def get(key: str) -> Optional[Any]:
        """Get value from cache."""
        client = await get_redis_client()
        try:
            value = await client.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    @staticmethod
    async def set(key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in cache."""
        client = await get_redis_client()
        try:
            return await client.setex(key, ttl, json.dumps(value, default=str))
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    @staticmethod
    async def delete(key: str) -> bool:
        """Delete key from cache."""
        return await invalidate_cache_key(key)
    
    @staticmethod
    async def delete_pattern(pattern: str) -> int:
        """Delete all keys matching pattern."""
        return await invalidate_cache_pattern(pattern)


async def reset_cache_metrics() -> dict:
    """Reset cache metrics counters. Useful for testing or fresh monitoring periods."""
    global cache_metrics
    old_metrics = cache_metrics.copy()
    cache_metrics.update({
        "hits": 0,
        "misses": 0,
        "errors": 0,
        "total_requests": 0,
        "cache_size": 0
    })
    logger.info("Cache metrics reset")
    return {
        "action": "reset_complete",
        "previous_metrics": old_metrics,
        "current_metrics": cache_metrics.copy()
    }


async def get_cache_health() -> dict:
    """Get cache health status for monitoring and alerts."""
    try:
        client = await get_redis_client()
        
        # Test basic connectivity
        if isinstance(client, MockRedisClient):
            await client.ping()
            status = "healthy_mock"
        else:
            await client.ping()
            status = "healthy"
        
        stats = await get_cache_stats()
        hit_rate = stats.get("application_hit_rate", 0)
        
        # Determine health status
        if hit_rate >= 80:
            health_status = "excellent"
        elif hit_rate >= 60:
            health_status = "good"
        elif hit_rate >= 40:
            health_status = "fair"
        else:
            health_status = "poor"
        
        return {
            "status": status,
            "health": health_status,
            "connected": True,
            "hit_rate": hit_rate,
            "total_requests": cache_metrics["total_requests"],
            "errors": cache_metrics["errors"],
            "cache_type": stats.get("type", "unknown")
        }
        
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        return {
            "status": "unhealthy",
            "health": "critical",
            "connected": False,
            "error": str(e),
            "hit_rate": 0,
            "total_requests": cache_metrics["total_requests"],
            "errors": cache_metrics.get("errors", 0) + 1
        }


# Export main components
__all__ = [
    'init_redis',
    'close_redis',
    'get_redis_client',
    'cache_key_wrapper',
    'invalidate_cache_pattern',
    'invalidate_cache_key',
    'get_cache_stats',
    'get_cache_health',
    'reset_cache_metrics',
    'CacheService'
]