"""
Unit tests for Cart Service layer.
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, patch
from uuid import uuid4
from datetime import datetime

from app.services.cart_service import CartService
from app.repositories.cart_repository import CartRepository
from app.models import Cart, CartItem, Product
from app.tests.fixtures.factories import CartFactory, CartItemFactory, ProductFactory


class TestCartService:
    """Test cases for CartService."""
    
    @pytest.fixture
    def mock_repository(self) -> Mock:
        """Create a mock CartRepository."""
        return Mock(spec=CartRepository)
    
    @pytest.fixture
    def service(self, mock_repository: Mock) -> CartService:
        """Create a CartService instance with mocked dependencies."""
        return CartService(repository=mock_repository)
    
    def test_add_product_to_cart_new_item(self, service: CartService, mock_repository: Mock):
        """Test adding a new product to cart."""
        # Setup
        user_id = uuid4()
        product_id = uuid4()
        quantity = 2
        
        cart = CartFactory(user_id=user_id)
        product = ProductFactory(product_id=product_id, unit_price=Decimal("45.99"))
        
        mock_repository.get_or_create_cart.return_value = cart
        mock_repository.get_cart_item.return_value = None  # Item doesn't exist
        mock_repository.add_cart_item.return_value = CartItemFactory(
            cart_id=cart.cart_id,
            product_id=product_id,
            quantity=quantity
        )
        
        # Execute
        result = service.add_product_to_cart(user_id, product_id, quantity)
        
        # Assert
        assert result is not None
        mock_repository.get_or_create_cart.assert_called_once_with(user_id)
        mock_repository.get_cart_item.assert_called_once_with(cart.cart_id, product_id)
        mock_repository.add_cart_item.assert_called_once_with(cart.cart_id, product_id, quantity)
    
    def test_add_product_to_cart_existing_item(self, service: CartService, mock_repository: Mock):
        """Test adding quantity to existing cart item."""
        # Setup
        user_id = uuid4()
        product_id = uuid4()
        additional_quantity = 2
        existing_quantity = 3
        
        cart = CartFactory(user_id=user_id)
        existing_item = CartItemFactory(
            cart_id=cart.cart_id,
            product_id=product_id,
            quantity=existing_quantity
        )
        updated_item = CartItemFactory(
            cart_id=cart.cart_id,
            product_id=product_id,
            quantity=existing_quantity + additional_quantity
        )
        
        mock_repository.get_or_create_cart.return_value = cart
        mock_repository.get_cart_item.return_value = existing_item
        mock_repository.update_cart_item_quantity.return_value = updated_item
        
        # Execute
        result = service.add_product_to_cart(user_id, product_id, additional_quantity)
        
        # Assert
        assert result is not None
        mock_repository.update_cart_item_quantity.assert_called_once_with(
            existing_item.cart_item_id,
            existing_quantity + additional_quantity
        )
    
    def test_update_cart_item_quantity_valid(self, service: CartService, mock_repository: Mock):
        """Test updating cart item quantity with valid quantity."""
        # Setup
        user_id = uuid4()
        cart_item_id = uuid4()
        new_quantity = 5
        
        cart_item = CartItemFactory(cart_item_id=cart_item_id, quantity=3)
        updated_item = CartItemFactory(cart_item_id=cart_item_id, quantity=new_quantity)
        
        mock_repository.get_cart_item_by_id.return_value = cart_item
        mock_repository.verify_cart_ownership.return_value = True
        mock_repository.update_cart_item_quantity.return_value = updated_item
        
        # Execute
        result = service.update_cart_item_quantity(user_id, cart_item_id, new_quantity)
        
        # Assert
        assert result == updated_item
        mock_repository.verify_cart_ownership.assert_called_once_with(cart_item.cart_id, user_id)
        mock_repository.update_cart_item_quantity.assert_called_once_with(cart_item_id, new_quantity)
    
    def test_update_cart_item_quantity_invalid_quantity(self, service: CartService, mock_repository: Mock):
        """Test updating cart item with invalid quantity."""
        # Setup
        user_id = uuid4()
        cart_item_id = uuid4()
        invalid_quantity = 0
        
        # Execute & Assert
        with pytest.raises(ValueError, match="Quantity must be greater than 0"):
            service.update_cart_item_quantity(user_id, cart_item_id, invalid_quantity)
    
    def test_update_cart_item_quantity_unauthorized(self, service: CartService, mock_repository: Mock):
        """Test updating cart item without ownership."""
        # Setup
        user_id = uuid4()
        cart_item_id = uuid4()
        new_quantity = 2
        
        cart_item = CartItemFactory(cart_item_id=cart_item_id)
        mock_repository.get_cart_item_by_id.return_value = cart_item
        mock_repository.verify_cart_ownership.return_value = False
        
        # Execute & Assert
        with pytest.raises(PermissionError, match="User does not own this cart"):
            service.update_cart_item_quantity(user_id, cart_item_id, new_quantity)
    
    def test_remove_cart_item_success(self, service: CartService, mock_repository: Mock):
        """Test removing cart item successfully."""
        # Setup
        user_id = uuid4()
        cart_item_id = uuid4()
        
        cart_item = CartItemFactory(cart_item_id=cart_item_id)
        mock_repository.get_cart_item_by_id.return_value = cart_item
        mock_repository.verify_cart_ownership.return_value = True
        mock_repository.remove_cart_item.return_value = True
        
        # Execute
        result = service.remove_cart_item(user_id, cart_item_id)
        
        # Assert
        assert result is True
        mock_repository.remove_cart_item.assert_called_once_with(cart_item_id)
    
    def test_remove_cart_item_not_found(self, service: CartService, mock_repository: Mock):
        """Test removing non-existent cart item."""
        # Setup
        user_id = uuid4()
        cart_item_id = uuid4()
        
        mock_repository.get_cart_item_by_id.return_value = None
        
        # Execute
        result = service.remove_cart_item(user_id, cart_item_id)
        
        # Assert
        assert result is False
        mock_repository.remove_cart_item.assert_not_called()
    
    def test_get_user_cart_with_items(self, service: CartService, mock_repository: Mock):
        """Test getting user cart with items."""
        # Setup
        user_id = uuid4()
        cart = CartFactory(user_id=user_id)
        cart_items = [
            CartItemFactory(cart_id=cart.cart_id, quantity=2),
            CartItemFactory(cart_id=cart.cart_id, quantity=1)
        ]
        
        mock_repository.get_user_cart.return_value = cart
        mock_repository.get_cart_items.return_value = cart_items
        
        # Execute
        result = service.get_user_cart(user_id)
        
        # Assert
        assert result is not None
        assert result["cart"] == cart
        assert result["items"] == cart_items
        assert result["total_items"] == 3  # 2 + 1
        
        mock_repository.get_user_cart.assert_called_once_with(user_id)
        mock_repository.get_cart_items.assert_called_once_with(cart.cart_id)
    
    def test_get_user_cart_empty(self, service: CartService, mock_repository: Mock):
        """Test getting empty user cart."""
        # Setup
        user_id = uuid4()
        
        mock_repository.get_user_cart.return_value = None
        
        # Execute
        result = service.get_user_cart(user_id)
        
        # Assert
        assert result is not None
        assert result["cart"] is None
        assert result["items"] == []
        assert result["total_items"] == 0
        assert result["total_price"] == Decimal("0.00")
    
    def test_calculate_cart_total(self, service: CartService, mock_repository: Mock):
        """Test calculating cart total with multiple items."""
        # Setup
        cart_id = uuid4()
        product1 = ProductFactory(unit_price=Decimal("45.99"))
        product2 = ProductFactory(unit_price=Decimal("29.99"))
        
        cart_items = [
            CartItemFactory(cart_id=cart_id, product_id=product1.product_id, quantity=2),
            CartItemFactory(cart_id=cart_id, product_id=product2.product_id, quantity=1)
        ]
        
        mock_repository.get_cart_items_with_products.return_value = [
            (cart_items[0], product1),
            (cart_items[1], product2)
        ]
        
        # Execute
        total = service.calculate_cart_total(cart_id)
        
        # Assert
        expected_total = (Decimal("45.99") * 2) + (Decimal("29.99") * 1)
        assert total == expected_total
    
    def test_clear_cart_success(self, service: CartService, mock_repository: Mock):
        """Test clearing cart successfully."""
        # Setup
        user_id = uuid4()
        cart = CartFactory(user_id=user_id)
        
        mock_repository.get_user_cart.return_value = cart
        mock_repository.clear_cart.return_value = True
        
        # Execute
        result = service.clear_cart(user_id)
        
        # Assert
        assert result is True
        mock_repository.clear_cart.assert_called_once_with(cart.cart_id)
    
    def test_clear_cart_not_found(self, service: CartService, mock_repository: Mock):
        """Test clearing non-existent cart."""
        # Setup
        user_id = uuid4()
        
        mock_repository.get_user_cart.return_value = None
        
        # Execute
        result = service.clear_cart(user_id)
        
        # Assert
        assert result is False
        mock_repository.clear_cart.assert_not_called()
    
    def test_merge_session_cart_with_user_cart(self, service: CartService, mock_repository: Mock):
        """Test merging session cart with user cart after login."""
        # Setup
        user_id = uuid4()
        session_id = "session123"
        
        user_cart = CartFactory(user_id=user_id)
        session_cart = CartFactory(session_id=session_id)
        
        session_items = [
            CartItemFactory(cart_id=session_cart.cart_id, quantity=2),
            CartItemFactory(cart_id=session_cart.cart_id, quantity=1)
        ]
        
        mock_repository.get_user_cart.return_value = user_cart
        mock_repository.get_session_cart.return_value = session_cart
        mock_repository.get_cart_items.return_value = session_items
        mock_repository.get_cart_item.side_effect = [None, None]  # No existing items
        mock_repository.add_cart_item.return_value = True
        mock_repository.delete_cart.return_value = True
        
        # Execute
        result = service.merge_session_cart(user_id, session_id)
        
        # Assert
        assert result is True
        assert mock_repository.add_cart_item.call_count == 2
        mock_repository.delete_cart.assert_called_once_with(session_cart.cart_id)
    
    def test_validate_cart_item_stock_availability(self, service: CartService, mock_repository: Mock):
        """Test validating cart items against stock availability."""
        # Setup
        cart_id = uuid4()
        
        product1 = ProductFactory(product_id=uuid4())
        product2 = ProductFactory(product_id=uuid4())
        
        cart_items = [
            CartItemFactory(cart_id=cart_id, product_id=product1.product_id, quantity=5),
            CartItemFactory(cart_id=cart_id, product_id=product2.product_id, quantity=2)
        ]
        
        mock_repository.get_cart_items.return_value = cart_items
        mock_repository.check_product_stock.side_effect = [
            {"available": True, "stock": 10},  # Product 1 has enough stock
            {"available": False, "stock": 1}   # Product 2 doesn't have enough stock
        ]
        
        # Execute
        validation_result = service.validate_cart_stock(cart_id)
        
        # Assert
        assert validation_result["valid"] is False
        assert len(validation_result["issues"]) == 1
        assert validation_result["issues"][0]["product_id"] == product2.product_id
        assert validation_result["issues"][0]["requested"] == 2
        assert validation_result["issues"][0]["available"] == 1
    
    def test_apply_discount_to_cart(self, service: CartService, mock_repository: Mock):
        """Test applying discount to cart."""
        # Setup
        cart_id = uuid4()
        discount_code = "SAVE10"
        discount_percentage = Decimal("10.00")
        cart_total = Decimal("100.00")
        
        mock_repository.validate_discount_code.return_value = {
            "valid": True,
            "discount_type": "percentage",
            "discount_value": discount_percentage
        }
        
        with patch.object(service, 'calculate_cart_total', return_value=cart_total):
            # Execute
            result = service.apply_discount(cart_id, discount_code)
            
            # Assert
            expected_discount = cart_total * (discount_percentage / 100)
            expected_final_total = cart_total - expected_discount
            
            assert result["discount_applied"] is True
            assert result["original_total"] == cart_total
            assert result["discount_amount"] == expected_discount
            assert result["final_total"] == expected_final_total
    
    def test_apply_invalid_discount_code(self, service: CartService, mock_repository: Mock):
        """Test applying invalid discount code."""
        # Setup
        cart_id = uuid4()
        invalid_code = "INVALID"
        
        mock_repository.validate_discount_code.return_value = {
            "valid": False,
            "reason": "Code not found"
        }
        
        # Execute
        result = service.apply_discount(cart_id, invalid_code)
        
        # Assert
        assert result["discount_applied"] is False
        assert result["error"] == "Code not found"
    
    def test_get_cart_summary_with_totals(self, service: CartService, mock_repository: Mock):
        """Test getting comprehensive cart summary."""
        # Setup
        user_id = uuid4()
        cart = CartFactory(user_id=user_id)
        
        product1 = ProductFactory(unit_price=Decimal("45.99"))
        product2 = ProductFactory(unit_price=Decimal("29.99"))
        
        cart_items = [
            CartItemFactory(cart_id=cart.cart_id, product_id=product1.product_id, quantity=2),
            CartItemFactory(cart_id=cart.cart_id, product_id=product2.product_id, quantity=1)
        ]
        
        mock_repository.get_user_cart.return_value = cart
        mock_repository.get_cart_items_with_products.return_value = [
            (cart_items[0], product1),
            (cart_items[1], product2)
        ]
        
        # Execute
        summary = service.get_cart_summary(user_id)
        
        # Assert
        assert summary["cart_id"] == cart.cart_id
        assert summary["total_items"] == 3  # 2 + 1
        assert summary["unique_items"] == 2
        assert summary["subtotal"] == Decimal("121.97")  # (45.99 * 2) + (29.99 * 1)
        assert len(summary["items"]) == 2
    
    @pytest.mark.asyncio
    async def test_async_cart_operations(self, service: CartService, mock_repository: Mock):
        """Test asynchronous cart operations."""
        # Setup
        user_id = uuid4()
        product_ids = [uuid4() for _ in range(5)]
        
        # Mock async repository methods
        async def mock_async_add_items(cart_id, items):
            return [CartItemFactory(cart_id=cart_id, product_id=item["product_id"]) for item in items]
        
        mock_repository.async_add_multiple_items.return_value = mock_async_add_items(
            uuid4(), 
            [{"product_id": pid, "quantity": 1} for pid in product_ids]
        )
        
        # Execute
        items_to_add = [{"product_id": pid, "quantity": 1} for pid in product_ids]
        result = await service.async_bulk_add_to_cart(user_id, items_to_add)
        
        # Assert
        assert len(result) == 5
        mock_repository.async_add_multiple_items.assert_called_once()
    
    def test_cart_expiry_cleanup(self, service: CartService, mock_repository: Mock):
        """Test cleaning up expired carts."""
        # Setup
        expired_days = 30
        mock_repository.cleanup_expired_carts.return_value = 15  # 15 carts cleaned up
        
        # Execute
        cleaned_count = service.cleanup_expired_carts(expired_days)
        
        # Assert
        assert cleaned_count == 15
        mock_repository.cleanup_expired_carts.assert_called_once_with(expired_days)