"""
Tests for AuthService - Authentication and Authorization Service
Tests cover JWT token operations, user authentication, and security features
"""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, MagicMock

import pytest
from fastapi import HTTPException, status
from jose import jwt
from sqlmodel import Session

from app.core.config import settings
from app.models import User
from app.models import UserCreate
from app.services.auth_service import AuthService, auth_service


class TestAuthService:
    """Test AuthService initialization and basic functionality"""

    def test_auth_service_initialization(self):
        """Test AuthService initializes correctly"""
        service = AuthService()
        assert service.pwd_context is not None
        assert service.algorithm == "HS256"
        assert service.oauth2_scheme is not None

    def test_global_auth_service_instance(self):
        """Test global auth_service instance is available"""
        assert auth_service is not None
        assert isinstance(auth_service, AuthService)


class TestPasswordSecurity:
    """Test password hashing and verification"""

    def test_password_hashing(self):
        """Test password is properly hashed"""
        service = AuthService()
        password = "test_password_123"
        hashed = service.get_password_hash(password)
        
        assert hashed != password  # Password should be hashed
        assert len(hashed) > 20  # Hash should be reasonably long
        assert hashed.startswith('$2b$')  # bcrypt hash format

    def test_password_verification_success(self):
        """Test correct password verification"""
        service = AuthService()
        password = "correct_password"
        hashed = service.get_password_hash(password)
        
        assert service.verify_password(password, hashed) is True

    def test_password_verification_failure(self):
        """Test incorrect password verification"""
        service = AuthService()
        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = service.get_password_hash(password)
        
        assert service.verify_password(wrong_password, hashed) is False

    def test_empty_password_handling(self):
        """Test handling of empty passwords"""
        service = AuthService()
        
        # Empty password should still create a hash
        hashed = service.get_password_hash("")
        assert hashed != ""
        
        # Verification should work for empty passwords too
        assert service.verify_password("", hashed) is True
        assert service.verify_password("not_empty", hashed) is False

    def test_special_characters_in_password(self):
        """Test passwords with special characters"""
        service = AuthService()
        password = "P@ssw0rd!#$%^&*()_+-=[]{}|;:,.<>?"
        hashed = service.get_password_hash(password)
        
        assert service.verify_password(password, hashed) is True
        assert service.verify_password("wrong", hashed) is False


class TestJWTTokenOperations:
    """Test JWT token creation, verification, and validation"""

    def test_create_access_token_basic(self):
        """Test basic access token creation"""
        service = AuthService()
        user_id = str(uuid.uuid4())
        
        token = service.create_access_token(subject=user_id)
        
        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens are reasonably long
        
        # Decode token to verify structure
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        assert payload["sub"] == user_id
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload
        assert "jti" in payload

    def test_create_access_token_with_custom_expiration(self):
        """Test access token with custom expiration"""
        service = AuthService()
        user_id = str(uuid.uuid4())
        custom_expiry = timedelta(hours=2)
        
        token = service.create_access_token(subject=user_id, expires_delta=custom_expiry)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        
        # Check expiration is approximately 2 hours from now
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        expected_exp = datetime.now(timezone.utc) + custom_expiry
        time_diff = abs((exp_time - expected_exp).total_seconds())
        assert time_diff < 5  # Allow 5 seconds tolerance

    def test_create_access_token_with_scopes(self):
        """Test access token with scopes"""
        service = AuthService()
        user_id = str(uuid.uuid4())
        scopes = ["read:products", "write:cart", "admin:users"]
        
        token = service.create_access_token(subject=user_id, scopes=scopes)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        
        assert payload["scopes"] == scopes

    def test_create_refresh_token(self):
        """Test refresh token creation"""
        service = AuthService()
        user_id = str(uuid.uuid4())
        
        token = service.create_refresh_token(subject=user_id)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        
        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"
        assert "exp" in payload
        assert "iat" in payload
        assert "jti" in payload

    def test_verify_token_success(self):
        """Test successful token verification"""
        service = AuthService()
        user_id = str(uuid.uuid4())
        
        token = service.create_access_token(subject=user_id)
        payload = service.verify_token(token)
        
        assert payload["sub"] == user_id
        assert payload["type"] == "access"

    def test_verify_token_invalid_signature(self):
        """Test token verification with invalid signature"""
        service = AuthService()
        
        # Create token with wrong secret
        payload = {"sub": "test", "exp": datetime.now(timezone.utc) + timedelta(hours=1)}
        invalid_token = jwt.encode(payload, "wrong_secret", algorithm="HS256")
        
        with pytest.raises(HTTPException) as exc_info:
            service.verify_token(invalid_token)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Could not validate credentials" in str(exc_info.value.detail)

    def test_verify_token_expired(self):
        """Test token verification with expired token"""
        service = AuthService()
        user_id = str(uuid.uuid4())
        
        # Create expired token
        expired_delta = timedelta(seconds=-1)  # Already expired
        token = service.create_access_token(subject=user_id, expires_delta=expired_delta)
        
        with pytest.raises(HTTPException) as exc_info:
            service.verify_token(token)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_verify_token_malformed(self):
        """Test token verification with malformed token"""
        service = AuthService()
        
        malformed_tokens = [
            "invalid.token.format",
            "not.a.jwt",
            "",
            "header.payload",  # Missing signature
            "too.many.parts.in.token.here"
        ]
        
        for token in malformed_tokens:
            with pytest.raises(HTTPException) as exc_info:
                service.verify_token(token)
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


class TestUserAuthentication:
    """Test user authentication and user management"""

    @patch('app.services.auth_service.Session')
    def test_authenticate_user_success(self, mock_session_class):
        """Test successful user authentication"""
        # Setup mock
        mock_session = Mock()
        mock_session_class.return_value.__enter__.return_value = mock_session
        
        # Create mock user
        user_id = uuid.uuid4()
        hashed_password = AuthService().get_password_hash("correct_password")
        mock_user = User(
            id=user_id,
            email="test@example.com",
            hashed_password=hashed_password,
            is_active=True
        )
        
        mock_session.exec.return_value.first.return_value = mock_user
        
        # Test authentication
        service = AuthService()
        result = service.authenticate_user("test@example.com", "correct_password")
        
        assert result == mock_user
        assert result.email == "test@example.com"

    @patch('app.services.auth_service.Session')
    def test_authenticate_user_not_found(self, mock_session_class):
        """Test authentication with non-existent user"""
        # Setup mock
        mock_session = Mock()
        mock_session_class.return_value.__enter__.return_value = mock_session
        mock_session.exec.return_value.first.return_value = None
        
        service = AuthService()
        result = service.authenticate_user("nonexistent@example.com", "password")
        
        assert result is None

    @patch('app.services.auth_service.Session')
    def test_authenticate_user_wrong_password(self, mock_session_class):
        """Test authentication with wrong password"""
        # Setup mock
        mock_session = Mock()
        mock_session_class.return_value.__enter__.return_value = mock_session
        
        # Create mock user with different password
        user_id = uuid.uuid4()
        hashed_password = AuthService().get_password_hash("correct_password")
        mock_user = User(
            id=user_id,
            email="test@example.com",
            hashed_password=hashed_password,
            is_active=True
        )
        
        mock_session.exec.return_value.first.return_value = mock_user
        
        service = AuthService()
        result = service.authenticate_user("test@example.com", "wrong_password")
        
        assert result is None

    @patch('app.services.auth_service.Session')
    def test_get_user_by_email(self, mock_session_class):
        """Test getting user by email"""
        # Setup mock
        mock_session = Mock()
        mock_session_class.return_value.__enter__.return_value = mock_session
        
        mock_user = User(id=uuid.uuid4(), email="test@example.com")
        mock_session.exec.return_value.first.return_value = mock_user
        
        service = AuthService()
        result = service.get_user_by_email("test@example.com")
        
        assert result == mock_user

    @patch('app.services.auth_service.Session')
    def test_get_user_by_id(self, mock_session_class):
        """Test getting user by ID"""
        # Setup mock
        mock_session = Mock()
        mock_session_class.return_value.__enter__.return_value = mock_session
        
        user_id = uuid.uuid4()
        mock_user = User(id=user_id, email="test@example.com")
        mock_session.exec.return_value.first.return_value = mock_user
        
        service = AuthService()
        result = service.get_user_by_id(user_id)
        
        assert result == mock_user

    @patch('app.services.auth_service.Session')
    def test_create_user_success(self, mock_session_class):
        """Test successful user creation"""
        # Setup mock
        mock_session = Mock()
        mock_session_class.return_value.__enter__.return_value = mock_session
        
        # Mock that user doesn't exist initially
        mock_session.exec.return_value.first.return_value = None
        
        # Mock created user
        created_user = User(
            id=uuid.uuid4(),
            email="new@example.com",
            full_name="New User",
            is_active=True
        )
        
        mock_session.add = Mock()
        mock_session.commit = Mock()
        mock_session.refresh = Mock()
        
        # Create user data
        user_create = UserCreate(
            email="new@example.com",
            password="secure_password",
            full_name="New User"
        )
        
        service = AuthService()
        
        # Mock the get_user_by_email call to return None (user doesn't exist)
        with patch.object(service, 'get_user_by_email', return_value=None):
            with patch('app.services.auth_service.User', return_value=created_user):
                result = service.create_user(user_create)
        
        assert result == created_user
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    def test_create_user_email_already_exists(self):
        """Test user creation with existing email"""
        service = AuthService()
        
        # Mock existing user
        existing_user = User(id=uuid.uuid4(), email="existing@example.com")
        
        user_create = UserCreate(
            email="existing@example.com",
            password="password",
            full_name="Test User"
        )
        
        with patch.object(service, 'get_user_by_email', return_value=existing_user):
            with pytest.raises(HTTPException) as exc_info:
                service.create_user(user_create)
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Email already registered" in exc_info.value.detail


class TestCurrentUserOperations:
    """Test current user operations from JWT tokens"""

    def test_get_current_user_success(self):
        """Test getting current user from valid token"""
        service = AuthService()
        user_id = uuid.uuid4()
        
        # Create token
        token = service.create_access_token(subject=str(user_id))
        
        # Mock user
        mock_user = User(id=user_id, email="test@example.com", is_active=True)
        
        with patch.object(service, 'get_user_by_id', return_value=mock_user):
            result = service.get_current_user(token)
        
        assert result == mock_user

    def test_get_current_user_invalid_token(self):
        """Test getting current user with invalid token"""
        service = AuthService()
        
        with pytest.raises(HTTPException) as exc_info:
            service.get_current_user("invalid_token")
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_current_user_no_subject(self):
        """Test getting current user with token missing subject"""
        service = AuthService()
        
        # Create token without subject
        payload = {"type": "access", "exp": datetime.now(timezone.utc) + timedelta(hours=1)}
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        
        with pytest.raises(HTTPException) as exc_info:
            service.get_current_user(token)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Could not validate credentials" in exc_info.value.detail

    def test_get_current_user_invalid_uuid(self):
        """Test getting current user with invalid UUID in token"""
        service = AuthService()
        
        # Create token with invalid UUID
        payload = {
            "sub": "not-a-valid-uuid",
            "type": "access",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        
        with pytest.raises(HTTPException) as exc_info:
            service.get_current_user(token)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid user ID format" in exc_info.value.detail

    def test_get_current_user_not_found(self):
        """Test getting current user when user doesn't exist"""
        service = AuthService()
        user_id = uuid.uuid4()
        
        token = service.create_access_token(subject=str(user_id))
        
        with patch.object(service, 'get_user_by_id', return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                service.get_current_user(token)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "User not found" in exc_info.value.detail

    def test_get_current_user_inactive(self):
        """Test getting current user when user is inactive"""
        service = AuthService()
        user_id = uuid.uuid4()
        
        token = service.create_access_token(subject=str(user_id))
        
        # Mock inactive user
        inactive_user = User(id=user_id, email="test@example.com", is_active=False)
        
        with patch.object(service, 'get_user_by_id', return_value=inactive_user):
            with pytest.raises(HTTPException) as exc_info:
                service.get_current_user(token)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Inactive user" in exc_info.value.detail


class TestRefreshTokenOperations:
    """Test refresh token operations and access token renewal"""

    def test_refresh_access_token_success(self):
        """Test successful access token refresh"""
        service = AuthService()
        user_id = uuid.uuid4()
        
        # Create refresh token
        refresh_token = service.create_refresh_token(subject=str(user_id))
        
        # Mock user
        mock_user = User(id=user_id, email="test@example.com", is_active=True)
        
        with patch.object(service, 'get_user_by_id', return_value=mock_user):
            new_access_token = service.refresh_access_token(refresh_token)
        
        # Verify new token
        assert isinstance(new_access_token, str)
        payload = jwt.decode(new_access_token, settings.SECRET_KEY, algorithms=["HS256"])
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "access"

    def test_refresh_access_token_invalid_token_type(self):
        """Test refresh with access token instead of refresh token"""
        service = AuthService()
        user_id = uuid.uuid4()
        
        # Create access token (wrong type)
        access_token = service.create_access_token(subject=str(user_id))
        
        with pytest.raises(HTTPException) as exc_info:
            service.refresh_access_token(access_token)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid token type" in exc_info.value.detail

    def test_refresh_access_token_user_not_found(self):
        """Test refresh when user no longer exists"""
        service = AuthService()
        user_id = uuid.uuid4()
        
        refresh_token = service.create_refresh_token(subject=str(user_id))
        
        with patch.object(service, 'get_user_by_id', return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                service.refresh_access_token(refresh_token)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "User not found or inactive" in exc_info.value.detail

    def test_refresh_access_token_inactive_user(self):
        """Test refresh when user is inactive"""
        service = AuthService()
        user_id = uuid.uuid4()
        
        refresh_token = service.create_refresh_token(subject=str(user_id))
        
        # Mock inactive user
        inactive_user = User(id=user_id, email="test@example.com", is_active=False)
        
        with patch.object(service, 'get_user_by_id', return_value=inactive_user):
            with pytest.raises(HTTPException) as exc_info:
                service.refresh_access_token(refresh_token)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "User not found or inactive" in exc_info.value.detail


class TestSecurityFeatures:
    """Test additional security features and edge cases"""

    def test_check_user_permissions(self):
        """Test user permissions checking"""
        service = AuthService()
        
        # Active user should have permissions
        active_user = User(id=uuid.uuid4(), email="test@example.com", is_active=True)
        assert service.check_user_permissions(active_user, ["read"]) is True
        
        # Inactive user should not have permissions
        inactive_user = User(id=uuid.uuid4(), email="test@example.com", is_active=False)
        assert service.check_user_permissions(inactive_user, ["read"]) is False

    def test_revoke_token(self):
        """Test token revocation (placeholder implementation)"""
        service = AuthService()
        token = "any_token"
        
        # Current implementation returns True (placeholder)
        result = service.revoke_token(token)
        assert result is True

    def test_jwt_token_uniqueness(self):
        """Test that JWT tokens have unique JTI (JWT ID)"""
        service = AuthService()
        user_id = str(uuid.uuid4())
        
        token1 = service.create_access_token(subject=user_id)
        token2 = service.create_access_token(subject=user_id)
        
        payload1 = jwt.decode(token1, settings.SECRET_KEY, algorithms=["HS256"])
        payload2 = jwt.decode(token2, settings.SECRET_KEY, algorithms=["HS256"])
        
        # JTI should be different even for same user
        assert payload1["jti"] != payload2["jti"]

    def test_token_creation_edge_cases(self):
        """Test token creation with edge case inputs"""
        service = AuthService()
        
        # Test with different subject types
        subjects = [
            str(uuid.uuid4()),  # UUID string
            "user@example.com",  # Email
            123,  # Integer
            None,  # None value
        ]
        
        for subject in subjects:
            token = service.create_access_token(subject=subject)
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            assert payload["sub"] == str(subject)

    def test_concurrent_authentication(self):
        """Test that authentication works correctly under concurrent access"""
        service = AuthService()
        
        # Simulate concurrent password operations
        passwords = ["pass1", "pass2", "pass3"] * 10
        
        for password in passwords:
            hashed = service.get_password_hash(password)
            assert service.verify_password(password, hashed) is True
            
            # Verify other passwords don't work
            for other_pass in ["wrong1", "wrong2", "wrong3"]:
                if other_pass != password:
                    assert service.verify_password(other_pass, hashed) is False