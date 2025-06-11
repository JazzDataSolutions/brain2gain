# backend/performance_optimizations/advanced_cache.py
"""
Advanced caching strategies with intelligent cache warming, 
hierarchical invalidation, and performance monitoring.
"""

import asyncio
import hashlib
import json
import logging
import time
from typing import Any, Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from functools import wraps
from dataclasses import dataclass, asdict

import redis.asyncio as redis
from redis.asyncio import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)

# ─── CACHE CONFIGURATION ──────────────────────────────────────────────────

@dataclass
class CacheConfig:
    """Cache configuration with intelligent defaults."""
    
    # Basic settings
    default_ttl: int = 300  # 5 minutes
    long_ttl: int = 3600    # 1 hour
    short_ttl: int = 60     # 1 minute
    
    # Cache warming
    enable_warming: bool = True
    warming_threshold: float = 0.8  # Warm cache when 80% of TTL elapsed
    max_warming_concurrent: int = 5
    
    # Memory management
    max_memory_mb: int = 512
    eviction_policy: str = "allkeys-lru"
    
    # Performance monitoring
    enable_metrics: bool = True
    slow_query_threshold: float = 1.0  # seconds
    
    # Compression
    enable_compression: bool = True
    compression_threshold: int = 1024  # bytes


cache_config = CacheConfig()


# ─── INTELLIGENT CACHE WRAPPER ────────────────────────────────────────────

class SmartCache:
    """Intelligent caching with warming, monitoring, and optimization."""
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.metrics = CacheMetrics()
        self._warming_tasks: Set[str] = set()
        self._warmer_semaphore = asyncio.Semaphore(cache_config.max_warming_concurrent)
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Get value with intelligent cache warming."""
        start_time = time.time()
        
        try:
            # Get value and TTL
            pipe = self.redis.pipeline()
            pipe.get(key)
            pipe.ttl(key)
            cached_value, ttl = await pipe.execute()
            
            if cached_value:
                self.metrics.record_hit(key, time.time() - start_time)
                
                # Check if we should warm the cache
                if cache_config.enable_warming and ttl > 0:
                    await self._maybe_warm_cache(key, ttl)
                
                return self._deserialize(cached_value)
            else:
                self.metrics.record_miss(key, time.time() - start_time)
                return default
                
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            self.metrics.record_error(key)
            return default
    
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value with optional compression."""
        try:
            ttl = ttl or cache_config.default_ttl
            serialized = self._serialize(value)
            
            # Apply compression if enabled and value is large enough
            if (cache_config.enable_compression and 
                len(serialized) > cache_config.compression_threshold):
                serialized = self._compress(serialized)
                key = f"compressed:{key}"
            
            await self.redis.setex(key, ttl, serialized)
            self.metrics.record_set(key, len(serialized))
            return True
            
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            self.metrics.record_error(key)
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete cache key."""
        try:
            deleted = await self.redis.delete(key)
            if deleted:
                self.metrics.record_delete(key)
            return bool(deleted)
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        deleted_count = 0
        try:
            async for key in self.redis.scan_iter(match=pattern):
                await self.redis.delete(key)
                deleted_count += 1
            
            if deleted_count > 0:
                self.metrics.record_pattern_delete(pattern, deleted_count)
            
            return deleted_count
        except Exception as e:
            logger.error(f"Cache pattern delete error for {pattern}: {e}")
            return 0
    
    async def _maybe_warm_cache(self, key: str, current_ttl: int):
        """Intelligently warm cache based on access patterns."""
        if key in self._warming_tasks:
            return  # Already warming
        
        # Calculate if we should warm based on TTL remaining
        original_ttl = await self._get_original_ttl(key)
        if original_ttl and current_ttl < (original_ttl * cache_config.warming_threshold):
            self._warming_tasks.add(key)
            asyncio.create_task(self._warm_cache_async(key))
    
    async def _warm_cache_async(self, key: str):
        """Asynchronously warm cache entry."""
        async with self._warmer_semaphore:
            try:
                # Here you would implement logic to refresh the cache
                # This is application-specific and would call the original function
                logger.debug(f"Warming cache for key: {key}")
                
                # Remove from warming tasks
                self._warming_tasks.discard(key)
                
            except Exception as e:
                logger.error(f"Cache warming error for key {key}: {e}")
                self._warming_tasks.discard(key)
    
    def _serialize(self, value: Any) -> str:
        """Serialize value for cache storage."""
        return json.dumps(value, default=str, separators=(',', ':'))
    
    def _deserialize(self, value: str) -> Any:
        """Deserialize value from cache."""
        return json.loads(value)
    
    def _compress(self, data: str) -> bytes:
        """Compress data if compression is enabled."""
        import gzip
        return gzip.compress(data.encode('utf-8'))
    
    def _decompress(self, data: bytes) -> str:
        """Decompress data."""
        import gzip
        return gzip.decompress(data).decode('utf-8')
    
    async def _get_original_ttl(self, key: str) -> Optional[int]:
        """Get original TTL for a key (would need to be stored separately)."""
        # This would require storing original TTL values
        # For now, return None
        return None


# ─── CACHE METRICS AND MONITORING ─────────────────────────────────────────

class CacheMetrics:
    """Cache performance metrics and monitoring."""
    
    def __init__(self):
        self.reset_metrics()
    
    def reset_metrics(self):
        """Reset all metrics."""
        self.hits = 0
        self.misses = 0
        self.errors = 0
        self.sets = 0
        self.deletes = 0
        self.total_response_time = 0.0
        self.slow_queries = 0
        self.key_sizes = []
        self.start_time = time.time()
    
    def record_hit(self, key: str, response_time: float):
        """Record cache hit."""
        self.hits += 1
        self.total_response_time += response_time
        if response_time > cache_config.slow_query_threshold:
            self.slow_queries += 1
            logger.warning(f"Slow cache hit for {key}: {response_time:.3f}s")
    
    def record_miss(self, key: str, response_time: float):
        """Record cache miss."""
        self.misses += 1
        self.total_response_time += response_time
    
    def record_error(self, key: str):
        """Record cache error."""
        self.errors += 1
        logger.error(f"Cache error for key: {key}")
    
    def record_set(self, key: str, size: int):
        """Record cache set operation."""
        self.sets += 1
        self.key_sizes.append(size)
    
    def record_delete(self, key: str):
        """Record cache delete."""
        self.deletes += 1
    
    def record_pattern_delete(self, pattern: str, count: int):
        """Record pattern delete operation."""
        logger.info(f"Deleted {count} keys matching pattern: {pattern}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        avg_response_time = (self.total_response_time / total_requests) if total_requests > 0 else 0
        avg_key_size = sum(self.key_sizes) / len(self.key_sizes) if self.key_sizes else 0
        
        return {
            "hit_rate_percent": round(hit_rate, 2),
            "total_hits": self.hits,
            "total_misses": self.misses,
            "total_errors": self.errors,
            "total_sets": self.sets,
            "total_deletes": self.deletes,
            "avg_response_time_ms": round(avg_response_time * 1000, 2),
            "slow_queries": self.slow_queries,
            "avg_key_size_bytes": round(avg_key_size, 2),
            "uptime_seconds": round(time.time() - self.start_time, 2),
            "error_rate_percent": round((self.errors / max(1, total_requests)) * 100, 2)
        }


# ─── HIERARCHICAL CACHE INVALIDATION ──────────────────────────────────────

class CacheHierarchy:
    """Manage hierarchical cache invalidation."""
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.dependencies: Dict[str, Set[str]] = {}
    
    async def add_dependency(self, parent_key: str, child_key: str):
        """Add cache dependency relationship."""
        deps_key = f"deps:{parent_key}"
        await self.redis.sadd(deps_key, child_key)
        await self.redis.expire(deps_key, 86400)  # 24 hours
    
    async def invalidate_hierarchy(self, parent_key: str) -> int:
        """Invalidate parent and all dependent cache keys."""
        invalidated = 0
        
        try:
            # Get all dependent keys
            deps_key = f"deps:{parent_key}"
            dependent_keys = await self.redis.smembers(deps_key)
            
            # Invalidate all dependent keys
            if dependent_keys:
                deleted = await self.redis.delete(*dependent_keys)
                invalidated += deleted
            
            # Invalidate parent key
            parent_deleted = await self.redis.delete(parent_key)
            invalidated += parent_deleted
            
            # Clean up dependencies
            await self.redis.delete(deps_key)
            
            logger.info(f"Invalidated {invalidated} cache keys in hierarchy for {parent_key}")
            return invalidated
            
        except Exception as e:
            logger.error(f"Error invalidating cache hierarchy for {parent_key}: {e}")
            return 0


# ─── CACHE PRELOADING AND WARMING ──────────────────────────────────────────

class CacheWarmer:
    """Proactive cache warming for critical data."""
    
    def __init__(self, smart_cache: SmartCache):
        self.cache = smart_cache
        self.warming_schedule: List[Tuple[str, callable, int]] = []  # (key, func, interval)
    
    def register_warmer(self, key_pattern: str, data_func: callable, interval: int = 300):
        """Register a function to warm specific cache keys."""
        self.warming_schedule.append((key_pattern, data_func, interval))
    
    async def warm_critical_caches(self):
        """Warm all registered critical caches."""
        tasks = []
        
        for key_pattern, data_func, interval in self.warming_schedule:
            task = asyncio.create_task(self._warm_cache_key(key_pattern, data_func, interval))
            tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _warm_cache_key(self, key: str, data_func: callable, ttl: int):
        """Warm specific cache key."""
        try:
            data = await data_func()
            await self.cache.set(key, data, ttl)
            logger.info(f"Warmed cache for key: {key}")
        except Exception as e:
            logger.error(f"Failed to warm cache for key {key}: {e}")


# ─── ADVANCED CACHE DECORATORS ─────────────────────────────────────────────

def adaptive_cache(
    key_prefix: str,
    ttl: int = None,
    condition: callable = None,
    invalidate_on: List[str] = None
):
    """
    Advanced cache decorator with adaptive TTL and conditional caching.
    
    Args:
        key_prefix: Cache key prefix
        ttl: Cache TTL (adaptive if None)
        condition: Function to determine if result should be cached
        invalidate_on: List of events that should invalidate this cache
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            key = _generate_smart_cache_key(key_prefix, args, kwargs)
            
            # Get from cache
            smart_cache = await get_smart_cache()
            cached_result = await smart_cache.get(key)
            
            if cached_result is not None:
                return cached_result
            
            # Execute function
            start_time = time.time()
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Determine if we should cache this result
            should_cache = True
            if condition:
                should_cache = condition(result, execution_time)
            
            if should_cache:
                # Adaptive TTL based on execution time
                adaptive_ttl = ttl or _calculate_adaptive_ttl(execution_time)
                await smart_cache.set(key, result, adaptive_ttl)
                
                # Set up invalidation dependencies
                if invalidate_on:
                    hierarchy = CacheHierarchy(smart_cache.redis)
                    for parent_key in invalidate_on:
                        await hierarchy.add_dependency(parent_key, key)
            
            return result
        
        return wrapper
    return decorator


def _generate_smart_cache_key(prefix: str, args: tuple, kwargs: dict) -> str:
    """Generate optimized cache key with hashing for large arguments."""
    key_parts = [prefix]
    
    # Handle arguments
    for arg in args:
        if hasattr(arg, '__dict__'):  # Object
            key_parts.append(f"obj:{hash(str(arg.__dict__))}")
        elif len(str(arg)) > 50:  # Long string/data
            key_parts.append(f"hash:{hashlib.md5(str(arg).encode()).hexdigest()[:8]}")
        else:
            key_parts.append(str(arg))
    
    # Handle keyword arguments
    for k, v in sorted(kwargs.items()):
        if v is not None:
            if len(str(v)) > 50:
                key_parts.append(f"{k}:hash:{hashlib.md5(str(v).encode()).hexdigest()[:8]}")
            else:
                key_parts.append(f"{k}:{v}")
    
    return ':'.join(key_parts)


def _calculate_adaptive_ttl(execution_time: float) -> int:
    """Calculate adaptive TTL based on function execution time."""
    if execution_time < 0.1:  # Fast queries
        return cache_config.short_ttl
    elif execution_time < 1.0:  # Medium queries
        return cache_config.default_ttl
    else:  # Slow queries
        return cache_config.long_ttl


# ─── SMART CACHE INSTANCE ──────────────────────────────────────────────────

_smart_cache_instance: Optional[SmartCache] = None

async def get_smart_cache() -> SmartCache:
    """Get or create smart cache instance."""
    global _smart_cache_instance
    
    if _smart_cache_instance is None:
        from app.core.cache import get_redis_client
        redis_client = await get_redis_client()
        _smart_cache_instance = SmartCache(redis_client)
    
    return _smart_cache_instance


# ─── USAGE EXAMPLES ────────────────────────────────────────────────────────

# Example usage in product service
@adaptive_cache(
    "products:expensive_calculation",
    condition=lambda result, exec_time: exec_time > 0.5,  # Only cache slow operations
    invalidate_on=["products:list", "products:*"]
)
async def expensive_product_calculation(product_id: int):
    """Example of expensive calculation that benefits from intelligent caching."""
    # Simulate expensive operation
    await asyncio.sleep(1)
    return {"product_id": product_id, "calculated_value": 42}


# Export components
__all__ = [
    'SmartCache',
    'CacheMetrics', 
    'CacheHierarchy',
    'CacheWarmer',
    'adaptive_cache',
    'get_smart_cache',
    'cache_config'
]