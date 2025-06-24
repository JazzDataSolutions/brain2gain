"""
Auth Service - Centralized authentication and authorization
Implements JWT tokens, OAuth2, and role-based access control
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlmodel import Session, select

from app.core.config import settings
from app.core.database import engine
from app.models import User
from app.schemas.user import UserCreate


class AuthService:
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.algorithm = "HS256"
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return self.pwd_context.hash(password)

    def create_access_token(
        self,
        subject: str | Any,
        expires_delta: timedelta | None = None,
        scopes: list[str] | None = None,
    ) -> str:
        """Create JWT access token with optional scopes"""
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )

        to_encode = {
            "exp": expire,
            "sub": str(subject),
            "type": "access",
            "iat": datetime.now(timezone.utc),
            "jti": str(uuid.uuid4()),  # JWT ID for token tracking
        }

        if scopes:
            to_encode["scopes"] = scopes

        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=self.algorithm
        )
        return encoded_jwt

    def create_refresh_token(
        self, subject: str | Any, expires_delta: timedelta | None = None
    ) -> str:
        """Create JWT refresh token"""
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(days=7)

        to_encode = {
            "exp": expire,
            "sub": str(subject),
            "type": "refresh",
            "iat": datetime.now(timezone.utc),
            "jti": str(uuid.uuid4()),  # JWT ID for token tracking
        }

        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=self.algorithm
        )
        return encoded_jwt

    def verify_token(self, token: str) -> dict:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[self.algorithm]
            )
            return payload
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Could not validate credentials: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def authenticate_user(self, email: str, password: str) -> User | None:
        """Authenticate user with email and password"""
        with Session(engine) as session:
            statement = select(User).where(User.email == email)
            user = session.exec(statement).first()

            if not user:
                return None

            if not self.verify_password(password, user.hashed_password):
                return None

            return user

    def get_user_by_email(self, email: str) -> User | None:
        """Get user by email"""
        with Session(engine) as session:
            statement = select(User).where(User.email == email)
            return session.exec(statement).first()

    def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        """Get user by ID"""
        with Session(engine) as session:
            statement = select(User).where(User.id == user_id)
            return session.exec(statement).first()

    def create_user(self, user_create: UserCreate) -> User:
        """Create new user"""
        # Check if user already exists
        if self.get_user_by_email(user_create.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        with Session(engine) as session:
            hashed_password = self.get_password_hash(user_create.password)

            user = User(
                email=user_create.email,
                full_name=user_create.full_name,
                hashed_password=hashed_password,
                is_active=True,
            )

            session.add(user)
            session.commit()
            session.refresh(user)
            return user

    def get_current_user(self, token: str) -> User:
        """Get current user from JWT token"""
        payload = self.verify_token(token)
        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )

        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user ID format",
            )

        user = self.get_user_by_id(user_uuid)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user"
            )

        return user

    def check_user_permissions(self, user: User, required_scopes: list[str]) -> bool:
        """Check if user has required permissions/scopes"""
        # TODO: Implement role-based access control
        # For now, return True for active users
        return user.is_active

    def revoke_token(self, token: str) -> bool:
        """Revoke a token (implement token blacklist)"""
        # TODO: Implement token blacklist with Redis
        # For now, return True
        return True

    def refresh_access_token(self, refresh_token: str) -> str:
        """Generate new access token from refresh token"""
        payload = self.verify_token(refresh_token)

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
            )

        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )

        # Verify user still exists and is active
        try:
            user_uuid = uuid.UUID(user_id)
            user = self.get_user_by_id(user_uuid)
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive",
                )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user ID format",
            )

        # Create new access token
        return self.create_access_token(subject=user_id)


# Global auth service instance
auth_service = AuthService()
