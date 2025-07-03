"""
Test cases for Orders API routes.
Critical path: Order management is core to the business logic.
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.main import app
from app.tests.utils.user import create_random_user
from app.tests.utils.utils import get_superuser_token_headers


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestOrderRoutes:
    """Test order API endpoints."""

    def test_create_order_from_cart(self, client: TestClient, db: Session):
        """Test creating order from cart items."""
        token_headers = get_superuser_token_headers()
        
        # First add items to cart
        cart_item = {"product_id": 1, "quantity": 2}
        client.post("/api/v1/cart/items", json=cart_item, headers=token_headers)
        
        # Create order from cart
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
        
        response = client.post(
            "/api/v1/orders/from-cart",
            json=order_data,
            headers=token_headers
        )
        assert response.status_code == 201
        
        order = response.json()
        assert order["status"] == "pending"
        assert len(order["items"]) == 1
        assert order["total_amount"] > 0

    def test_get_user_orders(self, client: TestClient, db: Session):
        """Test getting user's order history."""
        token_headers = get_superuser_token_headers()
        
        response = client.get("/api/v1/orders", headers=token_headers)
        assert response.status_code == 200
        
        orders = response.json()
        assert isinstance(orders, list)

    def test_get_order_by_id(self, client: TestClient, db: Session):
        """Test getting specific order details."""
        token_headers = get_superuser_token_headers()
        
        # Create an order first
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
        
        # Get order details
        response = client.get(f"/api/v1/orders/{order_id}", headers=token_headers)
        assert response.status_code == 200
        
        order = response.json()
        assert order["id"] == order_id

    def test_update_order_status(self, client: TestClient, db: Session):
        """Test updating order status (admin only)."""
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
        
        # Update status
        update_data = {"status": "processing"}
        response = client.put(
            f"/api/v1/orders/{order_id}/status",
            json=update_data,
            headers=token_headers
        )
        assert response.status_code == 200
        
        updated_order = response.json()
        assert updated_order["status"] == "processing"

    def test_cancel_order(self, client: TestClient, db: Session):
        """Test order cancellation."""
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
        
        # Cancel order
        response = client.put(
            f"/api/v1/orders/{order_id}/cancel",
            headers=token_headers
        )
        assert response.status_code == 200
        
        cancelled_order = response.json()
        assert cancelled_order["status"] == "cancelled"

    def test_get_order_analytics(self, client: TestClient, db: Session):
        """Test order analytics endpoint."""
        token_headers = get_superuser_token_headers()
        
        response = client.get("/api/v1/orders/analytics", headers=token_headers)
        assert response.status_code == 200
        
        analytics = response.json()
        assert "total_orders" in analytics
        assert "total_revenue" in analytics
        assert "orders_by_status" in analytics

    def test_create_order_with_invalid_address(self, client: TestClient, db: Session):
        """Test order creation with invalid shipping address."""
        token_headers = get_superuser_token_headers()
        
        # Add item to cart first
        cart_item = {"product_id": 1, "quantity": 1}
        client.post("/api/v1/cart/items", json=cart_item, headers=token_headers)
        
        # Try to create order with incomplete address
        order_data = {
            "shipping_address": {
                "street": "123 Test St"
                # Missing required fields
            },
            "payment_method": "credit_card"
        }
        
        response = client.post(
            "/api/v1/orders/from-cart",
            json=order_data,
            headers=token_headers
        )
        assert response.status_code == 422  # Validation error

    def test_create_order_with_empty_cart(self, client: TestClient, db: Session):
        """Test order creation with empty cart."""
        token_headers = get_superuser_token_headers()
        
        # Ensure cart is empty
        client.delete("/api/v1/cart", headers=token_headers)
        
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
        
        response = client.post(
            "/api/v1/orders/from-cart",
            json=order_data,
            headers=token_headers
        )
        assert response.status_code == 400  # Bad request

    def test_get_order_not_found(self, client: TestClient, db: Session):
        """Test getting non-existent order."""
        token_headers = get_superuser_token_headers()
        
        response = client.get("/api/v1/orders/99999", headers=token_headers)
        assert response.status_code == 404

    def test_update_order_status_invalid_transition(self, client: TestClient, db: Session):
        """Test invalid order status transitions."""
        token_headers = get_superuser_token_headers()
        
        # Create and cancel order first
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
        
        # Cancel order
        client.put(f"/api/v1/orders/{order_id}/cancel", headers=token_headers)
        
        # Try to update cancelled order to processing
        update_data = {"status": "processing"}
        response = client.put(
            f"/api/v1/orders/{order_id}/status",
            json=update_data,
            headers=token_headers
        )
        assert response.status_code == 400  # Should not allow invalid transition

    def test_order_unauthorized_access(self, client: TestClient):
        """Test order access without authentication."""
        response = client.get("/api/v1/orders")
        assert response.status_code == 401

    def test_order_pagination(self, client: TestClient, db: Session):
        """Test order list pagination."""
        token_headers = get_superuser_token_headers()
        
        # Test with pagination parameters
        response = client.get(
            "/api/v1/orders?skip=0&limit=10",
            headers=token_headers
        )
        assert response.status_code == 200
        
        orders = response.json()
        assert isinstance(orders, list)
        assert len(orders) <= 10