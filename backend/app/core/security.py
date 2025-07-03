from datetime import datetime, timedelta, timezone
from typing import Any, Set
import logging
import hashlib
import redis

import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

logger = logging.getLogger(__name__)

ALGORITHM = "HS256"

# JWT Blacklist using Redis for scalability
class TokenBlacklist:
    """
    JWT Token Blacklist implementation using Redis.
    Tracks revoked tokens to prevent reuse after logout/security incidents.
    """
    
    def __init__(self):
        self.redis_client = None
        self._connect_redis()
    
    def _connect_redis(self):
        """Connect to Redis for token blacklist storage."""
        try:
            import redis
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=1,  # Use DB 1 for blacklist (separate from main cache)
                decode_responses=True
            )
            # Test connection
            self.redis_client.ping()
            logger.info("✅ Redis connected for token blacklist")
        except Exception as e:
            logger.warning(f"⚠️ Redis not available for blacklist, using memory: {e}")
            self.redis_client = None
            # Fallback to in-memory set (not recommended for production)
            self._memory_blacklist: Set[str] = set()
    
    def _get_token_id(self, token: str) -> str:
        """Generate unique identifier for token."""
        return hashlib.sha256(token.encode()).hexdigest()[:16]
    
    def add_token(self, token: str, expires_at: datetime = None):
        """Add token to blacklist."""
        token_id = self._get_token_id(token)
        
        if self.redis_client:
            try:
                # Set expiration to token's actual expiry time
                if expires_at:
                    ttl = int((expires_at - datetime.now(timezone.utc)).total_seconds())
                    if ttl > 0:
                        self.redis_client.setex(f"blacklist:{token_id}", ttl, "revoked")
                else:
                    # Default 24 hour expiry if no expiration provided
                    self.redis_client.setex(f"blacklist:{token_id}", 86400, "revoked")
                
                logger.info(f"🚫 Token {token_id} added to blacklist")
            except Exception as e:
                logger.error(f"Failed to add token to Redis blacklist: {e}")
                # Fallback to memory
                self._memory_blacklist.add(token_id)
        else:
            # Memory fallback
            self._memory_blacklist.add(token_id)
    
    def is_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted."""
        token_id = self._get_token_id(token)
        
        if self.redis_client:
            try:
                return self.redis_client.exists(f"blacklist:{token_id}") > 0
            except Exception as e:
                logger.error(f"Failed to check Redis blacklist: {e}")
                # Fallback to memory
                return token_id in self._memory_blacklist
        else:
            # Memory fallback
            return token_id in self._memory_blacklist
    
    def revoke_all_user_tokens(self, user_id: str):
        """Revoke all tokens for a specific user (security incident response)."""
        try:
            if self.redis_client:
                # Add user to revoked users list with 24h expiry
                self.redis_client.setex(f"revoked_user:{user_id}", 86400, "revoked")
            logger.warning(f"🚨 All tokens revoked for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to revoke user tokens: {e}")
    
    def is_user_revoked(self, user_id: str) -> bool:
        """Check if all user tokens are revoked."""
        if self.redis_client:
            try:
                return self.redis_client.exists(f"revoked_user:{user_id}") > 0
            except Exception:
                return False
        return False

# Global blacklist instance
token_blacklist = TokenBlacklist()

# Session management
class SessionManager:
    """
    Session timeout and activity tracking.
    """
    
    def __init__(self):
        self.redis_client = None
        self._connect_redis()
    
    def _connect_redis(self):
        """Connect to Redis for session storage."""
        try:
            import redis
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=2,  # Use DB 2 for sessions
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info("✅ Redis connected for session management")
        except Exception as e:
            logger.warning(f"⚠️ Redis not available for sessions: {e}")
            self.redis_client = None
    
    def track_session(self, user_id: str, token_id: str, ip_address: str = None, user_agent: str = None):
        """Track user session activity."""
        if not self.redis_client:
            return
        
        try:
            session_data = {
                "user_id": user_id,
                "last_activity": datetime.now(timezone.utc).isoformat(),
                "ip_address": ip_address or "unknown",
                "user_agent": user_agent or "unknown",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Store session with 24h expiry
            self.redis_client.hset(f"session:{token_id}", mapping=session_data)
            self.redis_client.expire(f"session:{token_id}", 86400)
            
            # Track user's active sessions
            self.redis_client.sadd(f"user_sessions:{user_id}", token_id)
            self.redis_client.expire(f"user_sessions:{user_id}", 86400)
            
        except Exception as e:
            logger.error(f"Failed to track session: {e}")
    
    def update_activity(self, token_id: str):
        """Update last activity timestamp."""
        if not self.redis_client:
            return
        
        try:
            self.redis_client.hset(
                f"session:{token_id}", 
                "last_activity", 
                datetime.now(timezone.utc).isoformat()
            )
        except Exception as e:
            logger.error(f"Failed to update activity: {e}")
    
    def get_user_sessions(self, user_id: str) -> list:
        """Get all active sessions for user."""
        if not self.redis_client:
            return []
        
        try:
            session_ids = self.redis_client.smembers(f"user_sessions:{user_id}")
            sessions = []
            
            for session_id in session_ids:
                session_data = self.redis_client.hgetall(f"session:{session_id}")
                if session_data:
                    sessions.append({
                        "session_id": session_id,
                        **session_data
                    })
            
            return sessions
        except Exception as e:
            logger.error(f"Failed to get user sessions: {e}")
            return []
    
    def revoke_session(self, token_id: str):
        """Revoke specific session."""
        if not self.redis_client:
            return
        
        try:
            # Get user_id before deleting
            session_data = self.redis_client.hgetall(f"session:{token_id}")
            if session_data and "user_id" in session_data:
                user_id = session_data["user_id"]
                # Remove from user's active sessions
                self.redis_client.srem(f"user_sessions:{user_id}", token_id)
            
            # Delete session
            self.redis_client.delete(f"session:{token_id}")
            
        except Exception as e:
            logger.error(f"Failed to revoke session: {e}")

# Global session manager instance
session_manager = SessionManager()


def create_access_token(subject: str | Any, expires_delta: timedelta, additional_claims: dict = None) -> str:
    """
    Create JWT access token with enhanced security features.
    
    Args:
        subject: User identifier (usually user ID)
        expires_delta: Token expiration time
        additional_claims: Extra claims to include in token
    
    Returns:
        Encoded JWT token string
    """
    expire = datetime.now(timezone.utc) + expires_delta
    issued_at = datetime.now(timezone.utc)
    
    # Standard claims
    to_encode = {
        "exp": expire,
        "iat": issued_at,
        "sub": str(subject),
        "jti": hashlib.sha256(f"{subject}{issued_at.isoformat()}".encode()).hexdigest()[:16]  # JWT ID for blacklist
    }
    
    # Add additional claims if provided
    if additional_claims:
        to_encode.update(additional_claims)
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    
    # Track token creation
    logger.info(f"🔑 Token created for user {subject}, expires: {expire}")
    
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def decode_access_token(token: str, check_blacklist: bool = True) -> dict[str, Any] | None:
    """
    Decode and validate JWT access token with blacklist checking.
    
    Args:
        token: JWT token string
        check_blacklist: Whether to check token blacklist
    
    Returns:
        Decoded payload if valid, None otherwise
    """
    try:
        # First check if token is blacklisted
        if check_blacklist and token_blacklist.is_blacklisted(token):
            logger.warning("🚫 Attempted use of blacklisted token")
            return None
        
        # Decode token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        
        # Check if user is globally revoked
        if "sub" in payload and token_blacklist.is_user_revoked(payload["sub"]):
            logger.warning(f"🚫 Attempted use of revoked user token: {payload['sub']}")
            return None
        
        # Update session activity if token has JTI
        if "jti" in payload:
            session_manager.update_activity(payload["jti"])
        
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.info("⏰ Token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"🚫 Invalid token: {e}")
        return None


def revoke_token(token: str) -> bool:
    """
    Revoke a specific token by adding it to blacklist.
    
    Args:
        token: JWT token to revoke
    
    Returns:
        True if successfully revoked, False otherwise
    """
    try:
        # Decode to get expiration time
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False})
        expires_at = datetime.fromtimestamp(payload.get("exp", 0), tz=timezone.utc) if "exp" in payload else None
        
        # Add to blacklist
        token_blacklist.add_token(token, expires_at)
        
        # Revoke session
        if "jti" in payload:
            session_manager.revoke_session(payload["jti"])
        
        logger.info(f"🚫 Token revoked for user {payload.get('sub', 'unknown')}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to revoke token: {e}")
        return False


def revoke_all_user_tokens(user_id: str) -> bool:
    """
    Revoke all tokens for a specific user (security incident response).
    
    Args:
        user_id: User ID to revoke all tokens for
    
    Returns:
        True if successfully revoked, False otherwise
    """
    try:
        token_blacklist.revoke_all_user_tokens(user_id)
        logger.warning(f"🚨 All tokens revoked for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to revoke all user tokens: {e}")
        return False


def get_user_sessions(user_id: str) -> list:
    """Get all active sessions for a user."""
    return session_manager.get_user_sessions(user_id)


def create_session(user_id: str, token: str, ip_address: str = None, user_agent: str = None):
    """Create and track a new session."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False})
        token_id = payload.get("jti", hashlib.sha256(token.encode()).hexdigest()[:16])
        
        session_manager.track_session(user_id, token_id, ip_address, user_agent)
        logger.info(f"📋 Session created for user {user_id}")
        
    except Exception as e:
        logger.error(f"Failed to create session: {e}")


# Security utilities
def is_token_valid(token: str) -> tuple[bool, str]:
    """
    Comprehensive token validation.
    
    Returns:
        Tuple of (is_valid, reason)
    """
    if not token:
        return False, "No token provided"
    
    if token_blacklist.is_blacklisted(token):
        return False, "Token is blacklisted"
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        
        if token_blacklist.is_user_revoked(payload.get("sub", "")):
            return False, "User tokens are revoked"
        
        return True, "Token is valid"
        
    except jwt.ExpiredSignatureError:
        return False, "Token has expired"
    except jwt.InvalidTokenError:
        return False, "Token is invalid"


def get_token_info(token: str) -> dict:
    """Get information about a token without full validation."""
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[ALGORITHM], 
            options={"verify_exp": False}
        )
        
        return {
            "user_id": payload.get("sub"),
            "expires_at": datetime.fromtimestamp(payload.get("exp", 0), tz=timezone.utc) if "exp" in payload else None,
            "issued_at": datetime.fromtimestamp(payload.get("iat", 0), tz=timezone.utc) if "iat" in payload else None,
            "token_id": payload.get("jti"),
            "is_blacklisted": token_blacklist.is_blacklisted(token),
            "is_user_revoked": token_blacklist.is_user_revoked(payload.get("sub", ""))
        }
    except Exception as e:
        return {"error": str(e)}
