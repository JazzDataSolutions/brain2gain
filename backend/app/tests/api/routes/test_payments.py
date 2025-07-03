"""
Test cases for Payments API routes.
Critical path: Payment processing is essential for revenue generation.
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session
from unittest.mock import patch

from app.main import app
from app.tests.utils.user import create_random_user
from app.tests.utils.utils import get_superuser_token_headers


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestPaymentRoutes:
    """Test payment API endpoints."""

    def test_create_payment_intent(self, client: TestClient, db: Session):
        """Test creating payment intent for order."""
        token_headers = get_superuser_token_headers()
        
        # Create order first
        cart_item = {"product_id": 1, "quantity": 1}
        client.post("/api/v1/cart/items", json=cart_item, headers=token_headers)
        
        order_data = {
            "shipping_address": {
                "street": "123 Test St",
                "city": "Test City",
                "state": "Test State",
                "postal_code": "12345",
                "country": "Mexico"
            },
            "payment_method": "credit_card"
        }
        
        create_response = client.post(
            "/api/v1/orders/from-cart",
            json=order_data,
            headers=token_headers
        )
        order_id = create_response.json()["id"]
        
        # Create payment intent
        payment_data = {
            "order_id": order_id,
            "payment_method": "stripe",
            "currency": "mxn"
        }
        
        with patch('app.services.stripe_service.StripeService.create_payment_intent') as mock_stripe:
            mock_stripe.return_value = {
                "id": "pi_test123",
                "client_secret": "pi_test123_secret",
                "status": "requires_payment_method"
            }
            
            response = client.post(
                "/api/v1/payments/intent",
                json=payment_data,
                headers=token_headers
            )
            assert response.status_code == 201
            
            payment_intent = response.json()
            assert "client_secret" in payment_intent
            assert payment_intent["status"] == "requires_payment_method"

    def test_confirm_payment(self, client: TestClient, db: Session):
        """Test confirming payment for order."""
        token_headers = get_superuser_token_headers()
        
        payment_confirmation = {
            "payment_intent_id": "pi_test123",
            "payment_method_id": "pm_test123"
        }
        
        with patch('app.services.stripe_service.StripeService.confirm_payment') as mock_confirm:
            mock_confirm.return_value = {
                "id": "pi_test123",
                "status": "succeeded",
                "amount": 10000,
                "currency": "mxn"
            }
            
            response = client.post(
                "/api/v1/payments/confirm",
                json=payment_confirmation,
                headers=token_headers
            )
            assert response.status_code == 200
            
            payment = response.json()
            assert payment["status"] == "succeeded"

    def test_get_payment_methods(self, client: TestClient, db: Session):
        """Test getting user's saved payment methods."""
        token_headers = get_superuser_token_headers()
        
        response = client.get("/api/v1/payments/methods", headers=token_headers)
        assert response.status_code == 200
        
        payment_methods = response.json()
        assert isinstance(payment_methods, list)

    def test_save_payment_method(self, client: TestClient, db: Session):
        """Test saving new payment method."""
        token_headers = get_superuser_token_headers()
        
        payment_method_data = {
            "payment_method_id": "pm_test123",
            "type": "card",
            "last4": "4242",
            "brand": "visa",
            "exp_month": 12,
            "exp_year": 2025
        }
        
        with patch('app.services.stripe_service.StripeService.attach_payment_method') as mock_attach:
            mock_attach.return_value = True
            
            response = client.post(
                "/api/v1/payments/methods",
                json=payment_method_data,
                headers=token_headers
            )
            assert response.status_code == 201
            
            saved_method = response.json()
            assert saved_method["last4"] == "4242"
            assert saved_method["brand"] == "visa"

    def test_delete_payment_method(self, client: TestClient, db: Session):
        """Test deleting saved payment method."""
        token_headers = get_superuser_token_headers()
        
        payment_method_id = "pm_test123"
        
        with patch('app.services.stripe_service.StripeService.detach_payment_method') as mock_detach:
            mock_detach.return_value = True
            
            response = client.delete(
                f"/api/v1/payments/methods/{payment_method_id}",
                headers=token_headers
            )
            assert response.status_code == 200

    def test_process_webhook(self, client: TestClient, db: Session):
        """Test processing payment webhook."""
        webhook_data = {
            "id": "evt_test123",
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_test123",
                    "status": "succeeded",
                    "metadata": {
                        "order_id": "1"
                    }
                }
            }
        }
        
        with patch('app.services.stripe_service.StripeService.verify_webhook') as mock_verify:
            mock_verify.return_value = True
            
            response = client.post(
                "/api/v1/payments/webhook",
                json=webhook_data,
                headers={"stripe-signature": "test_signature"}
            )
            assert response.status_code == 200

    def test_get_payment_history(self, client: TestClient, db: Session):
        """Test getting user's payment history."""
        token_headers = get_superuser_token_headers()
        
        response = client.get("/api/v1/payments/history", headers=token_headers)
        assert response.status_code == 200
        
        payments = response.json()
        assert isinstance(payments, list)

    def test_refund_payment(self, client: TestClient, db: Session):
        """Test processing payment refund."""
        token_headers = get_superuser_token_headers()
        
        refund_data = {
            "payment_intent_id": "pi_test123",
            "amount": 5000,  # Partial refund
            "reason": "requested_by_customer"
        }
        
        with patch('app.services.stripe_service.StripeService.create_refund') as mock_refund:
            mock_refund.return_value = {
                "id": "re_test123",
                "amount": 5000,
                "status": "succeeded"
            }
            
            response = client.post(
                "/api/v1/payments/refund",
                json=refund_data,
                headers=token_headers
            )
            assert response.status_code == 200
            
            refund = response.json()
            assert refund["amount"] == 5000
            assert refund["status"] == "succeeded"

    def test_payment_analytics(self, client: TestClient, db: Session):
        """Test payment analytics endpoint."""
        token_headers = get_superuser_token_headers()
        
        response = client.get("/api/v1/payments/analytics", headers=token_headers)
        assert response.status_code == 200
        
        analytics = response.json()
        assert "total_revenue" in analytics
        assert "successful_payments" in analytics
        assert "failed_payments" in analytics

    def test_invalid_payment_intent(self, client: TestClient, db: Session):
        """Test creating payment intent with invalid data."""
        token_headers = get_superuser_token_headers()
        
        payment_data = {
            "order_id": 99999,  # Non-existent order
            "payment_method": "stripe",
            "currency": "mxn"
        }
        
        response = client.post(
            "/api/v1/payments/intent",
            json=payment_data,
            headers=token_headers
        )
        assert response.status_code == 404

    def test_payment_failure_handling(self, client: TestClient, db: Session):
        """Test handling payment failures."""
        token_headers = get_superuser_token_headers()
        
        payment_confirmation = {
            "payment_intent_id": "pi_test123",
            "payment_method_id": "pm_test123"
        }
        
        with patch('app.services.stripe_service.StripeService.confirm_payment') as mock_confirm:
            mock_confirm.return_value = {
                "id": "pi_test123",
                "status": "requires_action",
                "next_action": {
                    "type": "use_stripe_sdk"
                }
            }
            
            response = client.post(
                "/api/v1/payments/confirm",
                json=payment_confirmation,
                headers=token_headers
            )
            assert response.status_code == 200
            
            payment = response.json()
            assert payment["status"] == "requires_action"

    def test_unauthorized_payment_access(self, client: TestClient):
        """Test payment access without authentication."""
        response = client.get("/api/v1/payments/methods")
        assert response.status_code == 401

    def test_payment_method_validation(self, client: TestClient, db: Session):
        """Test payment method data validation."""
        token_headers = get_superuser_token_headers()
        
        invalid_payment_method = {
            "payment_method_id": "",  # Empty ID
            "type": "invalid_type",
            "last4": "invalid",
            "exp_month": 13,  # Invalid month
            "exp_year": 2020  # Past year
        }
        
        response = client.post(
            "/api/v1/payments/methods",
            json=invalid_payment_method,
            headers=token_headers
        )
        assert response.status_code == 422  # Validation error