# backend/performance_optimizations/advanced_rate_limiting.py
"""
Advanced rate limiting with Redis-based distributed limiting,
adaptive rates, and intelligent abuse detection.
"""

import asyncio
import hashlib
import json
import logging
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

import redis.asyncio as redis
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

logger = logging.getLogger(__name__)

# ─── RATE LIMITING CONFIGURATION ──────────────────────────────────────────

class RateLimitType(Enum):
    ANONYMOUS = "anonymous"
    AUTHENTICATED = "authenticated"
    PREMIUM = "premium"
    API_KEY = "api_key"
    ADMIN = "admin"

@dataclass
class RateLimitRule:
    """Rate limit rule configuration."""
    limit: int              # Requests per window
    window: int             # Window size in seconds
    burst_limit: int        # Burst allowance
    penalty_multiplier: float = 1.5  # Penalty for exceeding limits

# Default rate limit configurations
RATE_LIMIT_RULES = {
    RateLimitType.ANONYMOUS: RateLimitRule(20, 60, 5),
    RateLimitType.AUTHENTICATED: RateLimitRule(200, 60, 50),
    RateLimitType.PREMIUM: RateLimitRule(1000, 60, 200),
    RateLimitType.API_KEY: RateLimitRule(5000, 60, 1000),
    RateLimitType.ADMIN: RateLimitRule(10000, 60, 2000),
}

# ─── REDIS-BASED DISTRIBUTED RATE LIMITER ─────────────────────────────────

class DistributedRateLimiter:
    """Redis-based distributed rate limiter with sliding window."""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.lua_script = self._load_lua_script()
    
    def _load_lua_script(self) -> str:
        """Load Lua script for atomic rate limiting operations."""
        return """
        local key = KEYS[1]
        local window = tonumber(ARGV[1])
        local limit = tonumber(ARGV[2])
        local current_time = tonumber(ARGV[3])
        
        -- Remove expired entries
        redis.call('ZREMRANGEBYSCORE', key, '-inf', current_time - window)
        
        -- Get current count
        local current_count = redis.call('ZCARD', key)
        
        if current_count < limit then
            -- Add current request
            redis.call('ZADD', key, current_time, current_time)
            redis.call('EXPIRE', key, window)
            return {1, limit - current_count - 1}
        else
            return {0, 0}
        end
        """
    
    async def is_allowed(
        self, 
        identifier: str, 
        rule: RateLimitRule,
        current_time: float = None
    ) -> Tuple[bool, int, int]:
        """
        Check if request is allowed under rate limit.
        
        Returns:
            (is_allowed, remaining_requests, reset_time)
        """
        current_time = current_time or time.time()
        key = f"rate_limit:{identifier}"
        
        try:
            # Execute atomic Lua script
            result = await self.redis.eval(
                self.lua_script,
                1,  # Number of keys
                key,
                rule.window,
                rule.limit,
                current_time
            )
            
            is_allowed = bool(result[0])
            remaining = int(result[1])
            reset_time = int(current_time + rule.window)
            
            return is_allowed, remaining, reset_time
            
        except Exception as e:
            logger.error(f"Rate limiter error for {identifier}: {e}")
            # Fail open - allow request if Redis is down
            return True, rule.limit, int(current_time + rule.window)
    
    async def get_current_usage(self, identifier: str, window: int) -> int:
        """Get current usage count for identifier."""
        key = f"rate_limit:{identifier}"
        current_time = time.time()
        
        try:
            # Remove expired entries and count current
            await self.redis.zremrangebyscore(
                key, '-inf', current_time - window
            )
            return await self.redis.zcard(key)
        except Exception as e:
            logger.error(f"Error getting usage for {identifier}: {e}")
            return 0


# ─── ADAPTIVE RATE LIMITER ─────────────────────────────────────────────────

class AdaptiveRateLimiter:
    """Adaptive rate limiter that adjusts limits based on system load."""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.base_limiter = DistributedRateLimiter(redis_client)
        self.system_load_factor = 1.0
        self.last_load_check = 0
    
    async def is_allowed(
        self, 
        identifier: str, 
        base_rule: RateLimitRule,
        user_type: RateLimitType
    ) -> Tuple[bool, int, int, Dict]:
        """Check rate limit with adaptive adjustments."""
        
        # Update system load factor periodically
        await self._update_load_factor()
        
        # Adjust rule based on system load and user behavior
        adjusted_rule = await self._adjust_rule(identifier, base_rule, user_type)
        
        # Check base rate limit
        is_allowed, remaining, reset_time = await self.base_limiter.is_allowed(
            identifier, adjusted_rule
        )
        
        # Additional checks for suspicious behavior
        if is_allowed:
            is_allowed = await self._check_abuse_patterns(identifier)
        
        info = {
            "original_limit": base_rule.limit,
            "adjusted_limit": adjusted_rule.limit,
            "load_factor": self.system_load_factor,
            "user_type": user_type.value
        }
        
        return is_allowed, remaining, reset_time, info
    
    async def _update_load_factor(self):
        """Update system load factor based on various metrics."""
        current_time = time.time()
        
        # Only check load every 30 seconds
        if current_time - self.last_load_check < 30:
            return
        
        self.last_load_check = current_time
        
        try:
            # Get Redis metrics
            info = await self.redis.info()
            
            # Calculate load based on:
            # - Memory usage
            # - CPU usage
            # - Connection count
            # - Command rate
            
            memory_usage = info.get('used_memory', 0) / info.get('maxmemory', 1)
            connected_clients = info.get('connected_clients', 0)
            
            # Simple load calculation (can be made more sophisticated)
            load_factor = 1.0
            
            if memory_usage > 0.8:  # High memory usage
                load_factor *= 0.7
            elif memory_usage > 0.6:  # Medium memory usage
                load_factor *= 0.85
            
            if connected_clients > 100:  # High connection count
                load_factor *= 0.8
            
            self.system_load_factor = max(0.1, min(1.0, load_factor))
            
            logger.info(f"Updated system load factor: {self.system_load_factor}")
            
        except Exception as e:
            logger.error(f"Error updating load factor: {e}")
            self.system_load_factor = 1.0
    
    async def _adjust_rule(
        self, 
        identifier: str, 
        base_rule: RateLimitRule,
        user_type: RateLimitType
    ) -> RateLimitRule:
        """Adjust rate limit rule based on system load and user behavior."""
        
        # Apply system load factor
        adjusted_limit = int(base_rule.limit * self.system_load_factor)
        adjusted_burst = int(base_rule.burst_limit * self.system_load_factor)
        
        # Get user behavior score
        behavior_score = await self._get_user_behavior_score(identifier)
        
        # Adjust based on behavior (good users get more, bad users get less)
        if behavior_score > 0.8:  # Good user
            adjusted_limit = int(adjusted_limit * 1.2)
            adjusted_burst = int(adjusted_burst * 1.2)
        elif behavior_score < 0.3:  # Suspicious user
            adjusted_limit = int(adjusted_limit * 0.5)
            adjusted_burst = int(adjusted_burst * 0.5)
        
        return RateLimitRule(
            limit=max(1, adjusted_limit),
            window=base_rule.window,
            burst_limit=max(1, adjusted_burst),
            penalty_multiplier=base_rule.penalty_multiplier
        )
    
    async def _get_user_behavior_score(self, identifier: str) -> float:
        """Calculate user behavior score (0.0 = bad, 1.0 = good)."""
        try:
            # Get user statistics from last 24 hours
            stats_key = f"user_stats:{identifier}"
            stats = await self.redis.hgetall(stats_key)
            
            if not stats:
                return 0.5  # Neutral for new users
            
            # Calculate score based on various factors
            error_rate = float(stats.get('error_rate', 0))
            avg_response_time = float(stats.get('avg_response_time', 0))
            abuse_count = int(stats.get('abuse_count', 0))
            
            score = 1.0
            
            # Penalize high error rates
            if error_rate > 0.1:  # > 10% error rate
                score *= 0.5
            
            # Penalize abuse
            if abuse_count > 0:
                score *= max(0.1, 1.0 - (abuse_count * 0.2))
            
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            logger.error(f"Error calculating behavior score for {identifier}: {e}")
            return 0.5
    
    async def _check_abuse_patterns(self, identifier: str) -> bool:
        """Check for abuse patterns and block if detected."""
        try:
            # Check for rapid-fire requests
            rapid_fire_key = f"rapid_fire:{identifier}"
            current_time = time.time()
            
            # Count requests in last 10 seconds
            recent_count = await self.redis.zcount(
                rapid_fire_key,
                current_time - 10,
                current_time
            )
            
            if recent_count > 50:  # More than 50 requests in 10 seconds
                # Add to abuse counter
                stats_key = f"user_stats:{identifier}"
                await self.redis.hincrby(stats_key, 'abuse_count', 1)
                await self.redis.expire(stats_key, 86400)  # 24 hours
                
                logger.warning(f"Abuse detected for {identifier}: {recent_count} requests in 10s")
                return False
            
            # Add current request to tracking
            await self.redis.zadd(rapid_fire_key, {str(current_time): current_time})
            await self.redis.expire(rapid_fire_key, 60)
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking abuse patterns for {identifier}: {e}")
            return True  # Fail open


# ─── ADVANCED RATE LIMITING MIDDLEWARE ─────────────────────────────────────

class AdvancedRateLimitMiddleware(BaseHTTPMiddleware):
    """Advanced rate limiting middleware with Redis and adaptive features."""
    
    def __init__(self, app):
        super().__init__(app)
        self.redis_client = None
        self.rate_limiter = None
        self._initialized = False
    
    async def _init_redis(self):
        """Initialize Redis connection."""
        if not self._initialized:
            try:
                from app.core.cache import get_redis_client
                self.redis_client = await get_redis_client()
                self.rate_limiter = AdaptiveRateLimiter(self.redis_client)
                self._initialized = True
                logger.info("Advanced rate limiter initialized")
            except Exception as e:
                logger.error(f"Failed to initialize rate limiter: {e}")
                self.rate_limiter = None
    
    async def dispatch(self, request: Request, call_next):
        """Process request with advanced rate limiting."""
        
        # Initialize if needed
        if not self._initialized:
            await self._init_redis()
        
        # Skip rate limiting for certain endpoints
        if self._should_skip_rate_limiting(request):
            return await call_next(request)
        
        # If rate limiter failed to initialize, fall back to simple limiting
        if not self.rate_limiter:
            return await self._fallback_rate_limiting(request, call_next)
        
        # Get client identifier and type
        identifier, user_type = await self._get_client_info(request)
        
        # Get rate limit rule for user type
        base_rule = RATE_LIMIT_RULES.get(user_type, RATE_LIMIT_RULES[RateLimitType.ANONYMOUS])
        
        # Check rate limit
        is_allowed, remaining, reset_time, info = await self.rate_limiter.is_allowed(
            identifier, base_rule, user_type
        )
        
        if not is_allowed:
            return await self._create_rate_limit_response(
                base_rule, remaining, reset_time, info
            )
        
        # Process request
        start_time = time.time()
        response = await call_next(request)
        response_time = time.time() - start_time
        
        # Track user statistics
        await self._track_request_stats(identifier, response, response_time)
        
        # Add rate limit headers
        response.headers.update({
            "X-RateLimit-Limit": str(info["adjusted_limit"]),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_time),
            "X-RateLimit-Type": user_type.value,
            "X-RateLimit-LoadFactor": str(round(info["load_factor"], 2))
        })
        
        return response
    
    def _should_skip_rate_limiting(self, request: Request) -> bool:
        """Determine if rate limiting should be skipped."""
        skip_paths = {"/health", "/", "/docs", "/openapi.json", "/metrics"}
        return request.url.path in skip_paths
    
    async def _get_client_info(self, request: Request) -> Tuple[str, RateLimitType]:
        """Get client identifier and user type."""
        
        # Check for API key
        api_key = request.headers.get("X-API-Key")
        if api_key:
            # TODO: Validate API key and determine type
            return f"api_key:{hashlib.md5(api_key.encode()).hexdigest()}", RateLimitType.API_KEY
        
        # Check for authentication
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            # TODO: Decode token and get user info
            # For now, assume authenticated user
            user_id = hashlib.md5(token.encode()).hexdigest()[:16]
            return f"user:{user_id}", RateLimitType.AUTHENTICATED
        
        # Anonymous user - use IP + User-Agent
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("User-Agent", "")[:100]
        identifier = f"anon:{client_ip}:{hashlib.md5(user_agent.encode()).hexdigest()[:8]}"
        
        return identifier, RateLimitType.ANONYMOUS
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        # Check for forwarded headers (when behind proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        return request.client.host if request.client else "unknown"
    
    async def _track_request_stats(self, identifier: str, response, response_time: float):
        """Track request statistics for behavior analysis."""
        try:
            stats_key = f"user_stats:{identifier}"
            
            # Update statistics
            pipe = self.redis_client.pipeline()
            pipe.hincrby(stats_key, 'total_requests', 1)
            
            if 400 <= response.status_code < 600:
                pipe.hincrby(stats_key, 'error_count', 1)
            
            # Update average response time (simplified)
            pipe.hset(stats_key, 'last_response_time', response_time)
            pipe.expire(stats_key, 86400)  # 24 hours
            
            await pipe.execute()
            
        except Exception as e:
            logger.error(f"Error tracking stats for {identifier}: {e}")
    
    async def _create_rate_limit_response(
        self, 
        rule: RateLimitRule, 
        remaining: int, 
        reset_time: int,
        info: Dict
    ) -> JSONResponse:
        """Create rate limit exceeded response."""
        retry_after = reset_time - int(time.time())
        
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "Rate limit exceeded",
                "message": f"Too many requests. Limit: {info['adjusted_limit']} per {rule.window}s",
                "retry_after": retry_after,
                "limit": info["adjusted_limit"],
                "remaining": remaining,
                "reset": reset_time,
                "type": info["user_type"]
            },
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(info["adjusted_limit"]),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(reset_time)
            }
        )
    
    async def _fallback_rate_limiting(self, request: Request, call_next):
        """Fallback to simple in-memory rate limiting."""
        # Simple implementation for when Redis is unavailable
        # This would use the existing in-memory rate limiter
        logger.warning("Using fallback rate limiting - Redis unavailable")
        return await call_next(request)


# ─── RATE LIMIT ANALYTICS ──────────────────────────────────────────────────

class RateLimitAnalytics:
    """Analytics for rate limiting patterns and optimization."""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    async def get_top_rate_limited_ips(self, limit: int = 10) -> List[Dict]:
        """Get top rate-limited IP addresses."""
        try:
            # This would require tracking rate limit violations
            analytics_key = "rate_limit_violations"
            top_ips = await self.redis.zrevrange(
                analytics_key, 0, limit-1, withscores=True
            )
            
            return [
                {"ip": ip.decode(), "violations": int(score)}
                for ip, score in top_ips
            ]
        except Exception as e:
            logger.error(f"Error getting rate limit analytics: {e}")
            return []
    
    async def get_rate_limit_stats(self) -> Dict:
        """Get comprehensive rate limiting statistics."""
        try:
            stats = {}
            
            # Get current active rate limits
            pattern = "rate_limit:*"
            active_limits = 0
            async for key in self.redis.scan_iter(match=pattern):
                active_limits += 1
            
            stats["active_rate_limits"] = active_limits
            
            # Get violation stats
            violations_key = "rate_limit_violations"
            total_violations = await self.redis.zcard(violations_key)
            stats["total_violations_24h"] = total_violations
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting rate limit stats: {e}")
            return {}


# Export components
__all__ = [
    'DistributedRateLimiter',
    'AdaptiveRateLimiter', 
    'AdvancedRateLimitMiddleware',
    'RateLimitAnalytics',
    'RateLimitType',
    'RateLimitRule',
    'RATE_LIMIT_RULES'
]