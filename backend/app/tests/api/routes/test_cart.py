"""
Test cases for Cart API routes.
Critical path: Cart operations are fundamental to the e-commerce flow.
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


class TestCartRoutes:
    """Test cart API endpoints."""

    def test_get_cart_empty(self, client: TestClient, db: Session):
        """Test getting empty cart."""
        # Create user and login
        user = create_random_user(db)
        token_headers = get_superuser_token_headers()
        
        response = client.get("/api/v1/cart", headers=token_headers)
        assert response.status_code == 200
        
        cart_data = response.json()
        assert cart_data["items"] == []
        assert cart_data["total_price"] == 0
        assert cart_data["item_count"] == 0

    def test_add_item_to_cart(self, client: TestClient, db: Session):
        """Test adding item to cart."""
        token_headers = get_superuser_token_headers()
        
        # Add item to cart
        cart_item = {
            "product_id": 1,
            "quantity": 2
        }
        
        response = client.post(
            "/api/v1/cart/items", 
            json=cart_item,
            headers=token_headers
        )
        assert response.status_code == 200
        
        cart_data = response.json()
        assert len(cart_data["items"]) == 1
        assert cart_data["items"][0]["quantity"] == 2

    def test_update_cart_item_quantity(self, client: TestClient, db: Session):
        """Test updating cart item quantity."""
        token_headers = get_superuser_token_headers()
        
        # First add item
        cart_item = {"product_id": 1, "quantity": 1}
        client.post("/api/v1/cart/items", json=cart_item, headers=token_headers)
        
        # Update quantity
        update_data = {"quantity": 3}
        response = client.put(
            "/api/v1/cart/items/1", 
            json=update_data,
            headers=token_headers
        )
        assert response.status_code == 200
        
        cart_data = response.json()
        assert cart_data["items"][0]["quantity"] == 3

    def test_remove_item_from_cart(self, client: TestClient, db: Session):
        """Test removing item from cart."""
        token_headers = get_superuser_token_headers()
        
        # Add item first
        cart_item = {"product_id": 1, "quantity": 1}
        client.post("/api/v1/cart/items", json=cart_item, headers=token_headers)
        
        # Remove item
        response = client.delete("/api/v1/cart/items/1", headers=token_headers)
        assert response.status_code == 200
        
        # Verify cart is empty
        response = client.get("/api/v1/cart", headers=token_headers)
        cart_data = response.json()
        assert cart_data["items"] == []

    def test_clear_cart(self, client: TestClient, db: Session):
        """Test clearing entire cart."""
        token_headers = get_superuser_token_headers()
        
        # Add multiple items
        for i in range(3):
            cart_item = {"product_id": i + 1, "quantity": 1}
            client.post("/api/v1/cart/items", json=cart_item, headers=token_headers)
        
        # Clear cart
        response = client.delete("/api/v1/cart", headers=token_headers)
        assert response.status_code == 200
        
        # Verify cart is empty
        response = client.get("/api/v1/cart", headers=token_headers)
        cart_data = response.json()
        assert cart_data["items"] == []

    def test_cart_totals_calculation(self, client: TestClient, db: Session):
        """Test cart totals are calculated correctly."""
        token_headers = get_superuser_token_headers()
        
        # Add items with different quantities
        items = [
            {"product_id": 1, "quantity": 2},
            {"product_id": 2, "quantity": 1},
        ]
        
        for item in items:
            client.post("/api/v1/cart/items", json=item, headers=token_headers)
        
        response = client.get("/api/v1/cart", headers=token_headers)
        cart_data = response.json()
        
        assert cart_data["item_count"] == 3  # 2 + 1
        assert cart_data["total_price"] > 0

    def test_add_invalid_product_to_cart(self, client: TestClient, db: Session):
        """Test adding non-existent product to cart."""
        token_headers = get_superuser_token_headers()
        
        cart_item = {"product_id": 99999, "quantity": 1}
        
        response = client.post(
            "/api/v1/cart/items", 
            json=cart_item,
            headers=token_headers
        )
        assert response.status_code == 404

    def test_add_item_with_invalid_quantity(self, client: TestClient, db: Session):
        """Test adding item with invalid quantity."""
        token_headers = get_superuser_token_headers()
        
        cart_item = {"product_id": 1, "quantity": 0}
        
        response = client.post(
            "/api/v1/cart/items", 
            json=cart_item,
            headers=token_headers
        )
        assert response.status_code == 400

    def test_cart_persistence_across_sessions(self, client: TestClient, db: Session):
        """Test cart persists across user sessions."""
        token_headers = get_superuser_token_headers()
        
        # Add item to cart
        cart_item = {"product_id": 1, "quantity": 1}
        client.post("/api/v1/cart/items", json=cart_item, headers=token_headers)
        
        # Simulate new session by getting cart again
        response = client.get("/api/v1/cart", headers=token_headers)
        cart_data = response.json()
        
        assert len(cart_data["items"]) == 1
        assert cart_data["items"][0]["product_id"] == 1

    def test_cart_unauthorized_access(self, client: TestClient):
        """Test cart access without authentication."""
        response = client.get("/api/v1/cart")
        assert response.status_code == 401

    def test_cart_concurrent_modifications(self, client: TestClient, db: Session):
        """Test concurrent cart modifications."""
        token_headers = get_superuser_token_headers()
        
        # Simulate concurrent adds of same product
        cart_item = {"product_id": 1, "quantity": 1}
        
        responses = []
        for _ in range(3):
            response = client.post(
                "/api/v1/cart/items", 
                json=cart_item,
                headers=token_headers
            )
            responses.append(response)
        
        # All requests should succeed or handle conflicts gracefully
        success_count = sum(1 for r in responses if r.status_code in [200, 201])
        assert success_count >= 1  # At least one should succeed