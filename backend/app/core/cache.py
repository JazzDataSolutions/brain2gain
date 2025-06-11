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
                # Try to get cached result
                cached_value = await client.get(cache_key)
                if cached_value:
                    logger.debug(f"Cache HIT for key: {cache_key}")
                    return json.loads(cached_value)
                
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
    """Get basic cache statistics."""
    client = await get_redis_client()
    
    if isinstance(client, MockRedisClient):
        return {
            "type": "mock",
            "keys": len(client._data),
            "connected": True
        }
    
    try:
        info = await client.info()
        return {
            "type": "redis",
            "keys": info.get("db0", {}).get("keys", 0),
            "memory_used": info.get("used_memory_human", "N/A"),
            "connected_clients": info.get("connected_clients", 0),
            "total_commands": info.get("total_commands_processed", 0),
            "keyspace_hits": info.get("keyspace_hits", 0),
            "keyspace_misses": info.get("keyspace_misses", 0),
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return {"error": str(e), "connected": False}


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


# Export main components
__all__ = [
    'init_redis',
    'close_redis',
    'get_redis_client',
    'cache_key_wrapper',
    'invalidate_cache_pattern',
    'invalidate_cache_key',
    'get_cache_stats',
    'CacheService'
]