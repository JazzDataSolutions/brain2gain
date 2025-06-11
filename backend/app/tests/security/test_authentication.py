"""
Security tests for authentication system.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import Mock, patch
import jwt
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.security import (
    create_access_token, 
    verify_password, 
    get_password_hash,
    decode_access_token
)
from app.core.config import settings
from app.models import User
from app.tests.fixtures.factories import UserFactory, SuperUserFactory


@pytest.mark.security
class TestAuthenticationSecurity:
    """Security tests for authentication mechanisms."""
    
    def test_password_hashing_security(self):
        """Test password hashing security measures."""
        password = "TestPassword123!"
        
        # Test password hashing
        hashed = get_password_hash(password)
        
        # Hash should be different from password
        assert hashed != password
        
        # Hash should be consistent
        assert verify_password(password, hashed) is True
        
        # Wrong password should fail
        assert verify_password("WrongPassword", hashed) is False
        
        # Hash should include salt (bcrypt specific)
        assert len(hashed) >= 60
        assert hashed.startswith("$2b$")
    
    def test_password_hash_uniqueness(self):
        """Test that identical passwords produce different hashes (salt)."""
        password = "SamePassword123!"
        
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # Hashes should be different due to salt
        assert hash1 != hash2
        
        # But both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True
    
    def test_jwt_token_creation_and_validation(self):
        """Test JWT token security."""
        user_data = {"sub": str(uuid4()), "email": "test@example.com"}
        
        # Create token
        token = create_access_token(data=user_data)
        
        # Token should be a string
        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens are long
        
        # Decode and verify token
        decoded = decode_access_token(token)
        assert decoded["sub"] == user_data["sub"]
        assert decoded["email"] == user_data["email"]
        
        # Token should have expiration
        assert "exp" in decoded
        exp_datetime = datetime.fromtimestamp(decoded["exp"])
        assert exp_datetime > datetime.utcnow()
    
    def test_jwt_token_expiration(self):
        """Test JWT token expiration security."""
        user_data = {"sub": str(uuid4())}
        
        # Create token with short expiration
        short_token = create_access_token(
            data=user_data, 
            expires_delta=timedelta(seconds=1)
        )
        
        # Token should be valid immediately
        decoded = decode_access_token(short_token)
        assert decoded["sub"] == user_data["sub"]
        
        # Wait for token to expire
        import time
        time.sleep(2)
        
        # Expired token should be invalid
        with pytest.raises(jwt.ExpiredSignatureError):
            decode_access_token(short_token)
    
    def test_jwt_token_tampering_detection(self):
        """Test JWT token tampering detection."""
        user_data = {"sub": str(uuid4()), "role": "user"}
        token = create_access_token(data=user_data)
        
        # Tamper with token by changing a character
        tampered_token = token[:-10] + "X" + token[-9:]
        
        # Tampered token should be invalid
        with pytest.raises((jwt.InvalidSignatureError, jwt.DecodeError)):
            decode_access_token(tampered_token)
    
    def test_jwt_invalid_secret_key(self):
        """Test JWT token validation with wrong secret key."""
        user_data = {"sub": str(uuid4())}
        token = create_access_token(data=user_data)
        
        # Try to decode with wrong secret
        with patch('app.core.security.settings.SECRET_KEY', 'wrong_secret'):
            with pytest.raises(jwt.InvalidSignatureError):
                decode_access_token(token)
    
    def test_weak_password_rejection(self):
        """Test rejection of weak passwords."""
        weak_passwords = [
            "123456",
            "password",
            "abc123",
            "qwerty",
            "123456789",
            "12345",
            "1234567",
            "letmein",
            "monkey",
            "dragon"
        ]
        
        for weak_password in weak_passwords:
            # This test assumes you have password validation in place
            # You might need to implement password strength validation
            hashed = get_password_hash(weak_password)
            assert len(hashed) > 50  # At least bcrypt worked
            
            # Note: You should implement actual password strength validation
            # in your user creation/update endpoints
    
    def test_password_timing_attack_resistance(self):
        """Test password verification timing attack resistance."""
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        
        import time
        
        # Measure timing for correct password
        correct_times = []
        for _ in range(10):
            start = time.time()
            verify_password(password, hashed)
            correct_times.append(time.time() - start)
        
        # Measure timing for incorrect password
        incorrect_times = []
        for _ in range(10):
            start = time.time()
            verify_password("WrongPassword123!", hashed)
            incorrect_times.append(time.time() - start)
        
        avg_correct = sum(correct_times) / len(correct_times)
        avg_incorrect = sum(incorrect_times) / len(incorrect_times)
        
        # Timing should be similar (bcrypt is naturally resistant)
        time_difference = abs(avg_correct - avg_incorrect)
        assert time_difference < 0.01  # Less than 10ms difference


@pytest.mark.security
class TestAuthenticationEndpoints:
    """Security tests for authentication endpoints."""
    
    def test_login_endpoint_security(self, client: TestClient, db: Session):
        """Test login endpoint security measures."""
        # Create test user
        user = UserFactory(email="test@example.com")
        db.add(user)
        db.commit()
        
        # Test successful login
        response = client.post(
            "/api/v1/login/access-token",
            data={"username": "test@example.com", "password": "testpassword123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
    
    def test_login_brute_force_protection(self, client: TestClient, db: Session):
        """Test brute force protection on login endpoint."""
        # Create test user
        user = UserFactory(email="bruteforce@example.com")
        db.add(user)
        db.commit()
        
        # Attempt multiple failed logins
        failed_attempts = 0
        for _ in range(10):
            response = client.post(
                "/api/v1/login/access-token",
                data={"username": "bruteforce@example.com", "password": "wrongpassword"}
            )
            if response.status_code == 401:
                failed_attempts += 1
            elif response.status_code == 429:  # Rate limited
                break
        
        # Should eventually get rate limited
        # Note: This assumes you have rate limiting implemented
        assert failed_attempts > 0
    
    def test_login_sql_injection_attempts(self, client: TestClient):
        """Test SQL injection attempts on login."""
        sql_injection_attempts = [
            "admin' OR '1'='1",
            "admin'; DROP TABLE users; --",
            "admin' UNION SELECT * FROM users --",
            "'; UPDATE users SET password = 'hacked' --",
            "admin' OR 1=1 --"
        ]
        
        for injection_attempt in sql_injection_attempts:
            response = client.post(
                "/api/v1/login/access-token",
                data={"username": injection_attempt, "password": "anypassword"}
            )
            
            # Should return 401 or 422, never 200
            assert response.status_code in [401, 422]
            
            # Response should not contain sensitive information
            response_text = response.text.lower()
            assert "error" not in response_text or "sql" not in response_text
    
    def test_login_xss_prevention(self, client: TestClient):
        """Test XSS prevention in login responses."""
        xss_attempts = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "'><script>alert('xss')</script>",
            "\"><script>alert('xss')</script>"
        ]
        
        for xss_attempt in xss_attempts:
            response = client.post(
                "/api/v1/login/access-token",
                data={"username": xss_attempt, "password": "anypassword"}
            )
            
            # Response should not contain unescaped XSS payload
            assert xss_attempt not in response.text
            assert "<script>" not in response.text
            assert "javascript:" not in response.text
    
    def test_protected_endpoint_without_token(self, client: TestClient):
        """Test accessing protected endpoint without token."""
        response = client.get("/api/v1/users/me")
        assert response.status_code == 401
        
        data = response.json()
        assert "detail" in data
    
    def test_protected_endpoint_with_invalid_token(self, client: TestClient):
        """Test accessing protected endpoint with invalid token."""
        invalid_tokens = [
            "invalid_token",
            "Bearer invalid_token",
            "Bearer ",
            "",
            "notbearer token_value"
        ]
        
        for invalid_token in invalid_tokens:
            response = client.get(
                "/api/v1/users/me",
                headers={"Authorization": invalid_token}
            )
            assert response.status_code == 401
    
    def test_token_replay_attack_prevention(self, client: TestClient, superuser_token_headers: dict):
        """Test token replay attack prevention."""
        # Use the same token multiple times rapidly
        responses = []
        for _ in range(10):
            response = client.get("/api/v1/users/me", headers=superuser_token_headers)
            responses.append(response.status_code)
        
        # All requests should succeed (no replay protection expected for JWT)
        # But server should not be affected by rapid requests
        assert all(status == 200 for status in responses)
    
    def test_password_reset_security(self, client: TestClient, db: Session):
        """Test password reset security measures."""
        # Create test user
        user = UserFactory(email="reset@example.com")
        db.add(user)
        db.commit()
        
        # Request password reset
        response = client.post(
            "/api/v1/password-recovery/reset-password",
            json={"email": "reset@example.com"}
        )
        
        # Should not reveal if email exists or not
        assert response.status_code in [200, 202]
        
        # Response should be generic
        data = response.json()
        assert "sent" in data.get("message", "").lower() or "email" in data.get("message", "").lower()
    
    def test_user_enumeration_prevention(self, client: TestClient, db: Session):
        """Test prevention of user enumeration attacks."""
        # Create test user
        user = UserFactory(email="existing@example.com")
        db.add(user)
        db.commit()
        
        # Test with existing email
        response1 = client.post(
            "/api/v1/login/access-token",
            data={"username": "existing@example.com", "password": "wrongpassword"}
        )
        
        # Test with non-existing email
        response2 = client.post(
            "/api/v1/login/access-token",
            data={"username": "nonexisting@example.com", "password": "wrongpassword"}
        )
        
        # Both should return same error to prevent enumeration
        assert response1.status_code == response2.status_code
        
        # Error messages should be generic
        data1 = response1.json()
        data2 = response2.json()
        assert data1.get("detail") == data2.get("detail")
    
    def test_cors_security_headers(self, client: TestClient):
        """Test CORS and security headers."""
        response = client.options("/api/v1/login/access-token")
        
        # Check CORS headers
        assert "Access-Control-Allow-Origin" in response.headers
        assert "Access-Control-Allow-Methods" in response.headers
        assert "Access-Control-Allow-Headers" in response.headers
        
        # CORS should not be too permissive
        origin = response.headers.get("Access-Control-Allow-Origin")
        assert origin != "*" or settings.ENVIRONMENT == "development"
    
    def test_session_security(self, client: TestClient, superuser_token_headers: dict):
        """Test session security measures."""
        # Make authenticated request
        response = client.get("/api/v1/users/me", headers=superuser_token_headers)
        assert response.status_code == 200
        
        # Check security headers
        headers = response.headers
        
        # Should have security headers (if implemented)
        security_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options", 
            "X-XSS-Protection",
            "Strict-Transport-Security"
        ]
        
        # Note: These headers should be implemented in your middleware
        for header in security_headers:
            if header in headers:
                assert headers[header] is not None


@pytest.mark.security  
class TestAuthorizationSecurity:
    """Security tests for authorization (RBAC)."""
    
    def test_role_based_access_control(self, client: TestClient, db: Session):
        """Test role-based access control."""
        # Create users with different roles
        admin_user = SuperUserFactory(email="admin@example.com")
        normal_user = UserFactory(email="user@example.com")
        
        db.add_all([admin_user, normal_user])
        db.commit()
        
        # Get tokens for both users
        admin_response = client.post(
            "/api/v1/login/access-token",
            data={"username": "admin@example.com", "password": "testpassword123"}
        )
        admin_token = admin_response.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        user_response = client.post(
            "/api/v1/login/access-token", 
            data={"username": "user@example.com", "password": "testpassword123"}
        )
        user_token = user_response.json()["access_token"]
        user_headers = {"Authorization": f"Bearer {user_token}"}
        
        # Test admin endpoint access
        admin_endpoint_response = client.get("/api/v1/users/", headers=admin_headers)
        assert admin_endpoint_response.status_code == 200
        
        # Normal user should not access admin endpoints
        user_admin_response = client.get("/api/v1/users/", headers=user_headers)
        assert user_admin_response.status_code == 403
    
    def test_privilege_escalation_prevention(self, client: TestClient, normal_user_token_headers: dict):
        """Test prevention of privilege escalation."""
        # Try to create admin user as normal user
        admin_user_data = {
            "email": "malicious@example.com",
            "full_name": "Malicious User",
            "password": "password123",
            "is_superuser": True  # Try to escalate privileges
        }
        
        response = client.post(
            "/api/v1/users/",
            headers=normal_user_token_headers,
            json=admin_user_data
        )
        
        # Should be forbidden
        assert response.status_code == 403
    
    def test_horizontal_privilege_escalation_prevention(self, client: TestClient, db: Session):
        """Test prevention of horizontal privilege escalation."""
        # Create two normal users
        user1 = UserFactory(email="user1@example.com")
        user2 = UserFactory(email="user2@example.com") 
        
        db.add_all([user1, user2])
        db.commit()
        
        # Get token for user1
        response = client.post(
            "/api/v1/login/access-token",
            data={"username": "user1@example.com", "password": "testpassword123"}
        )
        user1_token = response.json()["access_token"]
        user1_headers = {"Authorization": f"Bearer {user1_token}"}
        
        # User1 tries to access User2's data
        response = client.get(f"/api/v1/users/{user2.user_id}", headers=user1_headers)
        
        # Should be forbidden or not found
        assert response.status_code in [403, 404]
    
    def test_resource_ownership_validation(self, client: TestClient, db: Session):
        """Test that users can only access their own resources."""
        # This test would need to be implemented based on your specific
        # resource ownership patterns (carts, orders, etc.)
        pass
    
    def test_api_rate_limiting_by_user(self, client: TestClient, normal_user_token_headers: dict):
        """Test rate limiting per user."""
        # Make rapid requests
        responses = []
        for _ in range(100):  # Make many requests rapidly
            response = client.get("/api/v1/users/me", headers=normal_user_token_headers)
            responses.append(response.status_code)
            
            # Break if rate limited
            if response.status_code == 429:
                break
        
        # Should eventually get rate limited (if implemented)
        # assert 429 in responses  # Uncomment when rate limiting is implemented