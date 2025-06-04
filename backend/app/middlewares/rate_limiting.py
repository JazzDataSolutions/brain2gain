"""
Rate limiting middleware for Brain2Gain API.

Provides protection against abuse and DoS attacks.
"""
import time
import logging
from typing import Dict, Tuple
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using in-memory storage.
    
    For production, consider using Redis for distributed rate limiting.
    """
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            app: FastAPI application
            calls: Number of calls allowed per period
            period: Time period in seconds
        """
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients: Dict[str, Tuple[int, float]] = {}
        
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier from request."""
        # Use X-Forwarded-For if behind proxy, otherwise use direct IP
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"
            
        # Include user agent for additional uniqueness
        user_agent = request.headers.get("User-Agent", "")[:50]
        return f"{client_ip}:{hash(user_agent) % 10000}"
    
    def _cleanup_expired_entries(self):
        """Remove expired entries from memory."""
        current_time = time.time()
        expired_clients = [
            client_id for client_id, (_, timestamp) in self.clients.items()
            if current_time - timestamp > self.period
        ]
        for client_id in expired_clients:
            del self.clients[client_id]
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        # Skip rate limiting for health checks and internal endpoints
        if request.url.path in ["/health", "/", "/docs", "/openapi.json"]:
            return await call_next(request)
            
        client_id = self._get_client_id(request)
        current_time = time.time()
        
        # Cleanup expired entries periodically
        if len(self.clients) > 1000:  # Prevent memory bloat
            self._cleanup_expired_entries()
        
        # Check if client exists and is within rate limit
        if client_id in self.clients:
            call_count, first_call_time = self.clients[client_id]
            
            # Reset counter if period has passed
            if current_time - first_call_time > self.period:
                self.clients[client_id] = (1, current_time)
            else:
                # Check if limit exceeded
                if call_count >= self.calls:
                    retry_after = int(self.period - (current_time - first_call_time) + 1)
                    
                    logger.warning(
                        f"Rate limit exceeded for client {client_id}",
                        extra={
                            "client_id": client_id,
                            "calls": call_count,
                            "period": self.period,
                            "retry_after": retry_after
                        }
                    )
                    
                    return JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={
                            "detail": "Too many requests",
                            "retry_after": retry_after,
                            "limit": self.calls,
                            "period": self.period
                        },
                        headers={"Retry-After": str(retry_after)}
                    )
                
                # Increment counter
                self.clients[client_id] = (call_count + 1, first_call_time)
        else:
            # New client
            self.clients[client_id] = (1, current_time)
        
        # Add rate limit headers to response
        response = await call_next(request)
        
        if client_id in self.clients:
            call_count, first_call_time = self.clients[client_id]
            remaining = max(0, self.calls - call_count)
            reset_time = int(first_call_time + self.period)
            
            response.headers["X-RateLimit-Limit"] = str(self.calls)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(reset_time)
        
        return response


class AuthenticatedRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting with different limits for authenticated vs anonymous users.
    """
    
    def __init__(self, app, 
                 anonymous_calls: int = 20, 
                 authenticated_calls: int = 200, 
                 period: int = 60):
        super().__init__(app)
        self.anonymous_calls = anonymous_calls
        self.authenticated_calls = authenticated_calls
        self.period = period
        self.clients: Dict[str, Tuple[int, float, bool]] = {}
    
    def _get_client_id(self, request: Request) -> Tuple[str, bool]:
        """Get client identifier and authentication status."""
        # Check if user is authenticated
        auth_header = request.headers.get("Authorization")
        is_authenticated = bool(auth_header and auth_header.startswith("Bearer "))
        
        # Use different identifiers for auth vs unauth users
        if is_authenticated:
            # For authenticated users, use token hash
            token = auth_header.split(" ")[1] if len(auth_header.split(" ")) > 1 else ""
            client_id = f"auth:{hash(token) % 100000}"
        else:
            # For anonymous users, use IP + user agent
            forwarded_for = request.headers.get("X-Forwarded-For")
            if forwarded_for:
                client_ip = forwarded_for.split(",")[0].strip()
            else:
                client_ip = request.client.host if request.client else "unknown"
            
            user_agent = request.headers.get("User-Agent", "")[:50]
            client_id = f"anon:{client_ip}:{hash(user_agent) % 10000}"
        
        return client_id, is_authenticated
    
    async def dispatch(self, request: Request, call_next):
        """Process request with tiered rate limiting."""
        # Skip rate limiting for certain endpoints
        if request.url.path in ["/health", "/", "/docs", "/openapi.json"]:
            return await call_next(request)
        
        client_id, is_authenticated = self._get_client_id(request)
        current_time = time.time()
        
        # Determine rate limit based on authentication
        limit = self.authenticated_calls if is_authenticated else self.anonymous_calls
        
        # Check rate limit
        if client_id in self.clients:
            call_count, first_call_time, _ = self.clients[client_id]
            
            if current_time - first_call_time > self.period:
                self.clients[client_id] = (1, current_time, is_authenticated)
            else:
                if call_count >= limit:
                    retry_after = int(self.period - (current_time - first_call_time) + 1)
                    
                    return JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={
                            "detail": "Too many requests",
                            "retry_after": retry_after,
                            "limit": limit,
                            "period": self.period,
                            "authenticated": is_authenticated
                        },
                        headers={"Retry-After": str(retry_after)}
                    )
                
                self.clients[client_id] = (call_count + 1, first_call_time, is_authenticated)
        else:
            self.clients[client_id] = (1, current_time, is_authenticated)
        
        response = await call_next(request)
        
        # Add headers
        if client_id in self.clients:
            call_count, first_call_time, _ = self.clients[client_id]
            remaining = max(0, limit - call_count)
            reset_time = int(first_call_time + self.period)
            
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(reset_time)
            response.headers["X-RateLimit-Type"] = "authenticated" if is_authenticated else "anonymous"
        
        return response