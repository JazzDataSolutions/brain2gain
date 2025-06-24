"""
Unit tests for security functions.
Tests password hashing, JWT token creation/validation.
"""

from datetime import timedelta
import pytest
import jwt
from app.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
    ALGORITHM
)
from app.core.config import settings


class TestPasswordSecurity:
    """Test password hashing and verification."""
    
    def test_password_hashing(self):
        """Test password hashing creates different hashes for same password."""
        password = "test_password_123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # Hashes should be different due to salt
        assert hash1 != hash2
        assert len(hash1) > 50  # bcrypt hashes are long
        
    def test_password_verification_success(self):
        """Test password verification with correct password."""
        password = "secure_password_456"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
        
    def test_password_verification_failure(self):
        """Test password verification with incorrect password."""
        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = get_password_hash(password)
        
        assert verify_password(wrong_password, hashed) is False
        
    def test_empty_password_handling(self):
        """Test handling of empty passwords."""
        empty_password = ""
        hashed = get_password_hash(empty_password)
        
        assert verify_password(empty_password, hashed) is True
        assert verify_password("not_empty", hashed) is False


class TestJWTSecurity:
    """Test JWT token creation and validation."""
    
    def test_token_creation(self):
        """Test JWT token creation."""
        subject = "test_user_123"
        expires_delta = timedelta(minutes=30)
        
        token = create_access_token(subject, expires_delta)
        
        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens are reasonably long
        
    def test_token_decoding_success(self):
        """Test successful JWT token decoding."""
        subject = "test_user_456"
        expires_delta = timedelta(minutes=30)
        
        token = create_access_token(subject, expires_delta)
        payload = decode_access_token(token)
        
        assert payload is not None
        assert payload["sub"] == subject
        assert "exp" in payload
        
    def test_token_decoding_invalid_token(self):
        """Test JWT token decoding with invalid token."""
        invalid_token = "invalid.jwt.token"
        
        payload = decode_access_token(invalid_token)
        
        assert payload is None
        
    def test_token_decoding_malformed_token(self):
        """Test JWT token decoding with malformed token."""
        malformed_token = "not_a_jwt_token_at_all"
        
        payload = decode_access_token(malformed_token)
        
        assert payload is None
        
    def test_token_with_expired_signature(self):
        """Test JWT token decoding with expired token."""
        subject = "test_user_789"
        # Create token that expires immediately
        expires_delta = timedelta(seconds=-1)
        
        token = create_access_token(subject, expires_delta)
        payload = decode_access_token(token)
        
        # Should return None for expired token
        assert payload is None
        
    def test_token_algorithm_consistency(self):
        """Test that token uses correct algorithm."""
        subject = "test_user_algorithm"
        expires_delta = timedelta(minutes=15)
        
        token = create_access_token(subject, expires_delta)
        
        # Decode manually to check algorithm
        header = jwt.get_unverified_header(token)
        assert header["alg"] == ALGORITHM
        
    def test_token_with_different_subjects(self):
        """Test tokens with different subjects."""
        subjects = ["user1", "user2", "admin@example.com", "123456"]
        expires_delta = timedelta(minutes=15)
        
        for subject in subjects:
            token = create_access_token(subject, expires_delta)
            payload = decode_access_token(token)
            
            assert payload is not None
            assert payload["sub"] == subject
            
    def test_token_secret_key_dependency(self):
        """Test that token validation depends on secret key."""
        subject = "test_user_secret"
        expires_delta = timedelta(minutes=30)
        
        token = create_access_token(subject, expires_delta)
        
        # Try to decode with wrong secret (should fail)
        try:
            jwt.decode(token, "wrong_secret", algorithms=[ALGORITHM])
            assert False, "Should have failed with wrong secret"
        except jwt.InvalidTokenError:
            # Expected behavior
            pass
            
        # Decode with correct secret through our function
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == subject


class TestSecurityIntegration:
    """Integration tests for security functions."""
    
    def test_password_token_workflow(self):
        """Test complete password and token workflow."""
        # User registration workflow
        original_password = "user_registration_password"
        user_id = "user_12345"
        
        # Hash password (as would happen during registration)
        hashed_password = get_password_hash(original_password)
        
        # Login workflow - verify password
        login_successful = verify_password(original_password, hashed_password)
        assert login_successful is True
        
        # Create access token after successful login
        token = create_access_token(user_id, timedelta(hours=1))
        
        # Validate token (as would happen on protected routes)
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == user_id
        
    def test_security_with_real_world_passwords(self):
        """Test security with various real-world password patterns."""
        passwords = [
            "Simple123",
            "Very_Complex_P@ssw0rd!",
            "short",
            "a" * 50,  # long password (but within bcrypt limits)
            "Пароль123",  # Unicode characters
            "pass with spaces",
            "🔒secure🔑password🛡️",  # Emoji
        ]
        
        for password in passwords:
            hashed = get_password_hash(password)
            assert verify_password(password, hashed) is True
            # For passwords shorter than bcrypt limit, wrong passwords should fail
            if len(password.encode('utf-8')) < 72:  # bcrypt limit
                assert verify_password(password + "wrong", hashed) is False
            
    def test_concurrent_token_creation(self):
        """Test that concurrent token creation works correctly."""
        import threading
        
        subjects = [f"user_{i}" for i in range(10)]
        tokens = [None] * 10
        expires_delta = timedelta(minutes=30)
        
        def create_token_for_user(index):
            tokens[index] = create_access_token(subjects[index], expires_delta)
        
        # Create tokens concurrently
        threads = []
        for i in range(10):
            thread = threading.Thread(target=create_token_for_user, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Verify all tokens are valid and unique
        for i, token in enumerate(tokens):
            assert token is not None
            payload = decode_access_token(token)
            assert payload is not None
            assert payload["sub"] == subjects[i]
        
        # All tokens should be different
        assert len(set(tokens)) == 10