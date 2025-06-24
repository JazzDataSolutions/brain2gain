"""
Tests for CartService - Shopping Cart Management Service
Tests cover cart creation, item management, cart operations, and calculations
"""

import uuid
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import Cart, CartItem, Product, ProductStatus
from app.schemas.cart import AddToCartRequest, CartRead, UpdateCartItemRequest
from app.services.cart_service import CartService

# Mark all async tests in this module
pytestmark = pytest.mark.asyncio


class TestCartServiceInitialization:
    """Test CartService initialization and basic functionality"""

    async def test_cart_service_initialization(self):
        """Test CartService initializes correctly"""
        mock_session = Mock(spec=AsyncSession)
        
        service = CartService(mock_session)
        
        assert service.session == mock_session
        assert service.cart_repo is not None
        assert service.product_repo is not None


class TestCartCreationAndRetrieval:
    """Test cart creation and retrieval functionality"""

    async def test_get_or_create_cart_for_user_existing(self):
        """Test getting existing cart for user"""
        mock_session = Mock(spec=AsyncSession)
        service = CartService(mock_session)
        
        user_id = uuid.uuid4()
        existing_cart = Cart(
            cart_id=1,
            user_id=user_id,
            session_id=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Mock repository method
        service.cart_repo.get_cart_by_user = AsyncMock(return_value=existing_cart)
        
        result = await service.get_or_create_cart(user_id=user_id)
        
        assert result == existing_cart
        service.cart_repo.get_cart_by_user.assert_called_once_with(user_id)

    async def test_get_or_create_cart_for_user_new(self):
        """Test creating new cart for user"""
        mock_session = Mock(spec=AsyncSession)
        service = CartService(mock_session)
        
        user_id = uuid.uuid4()
        new_cart = Cart(
            cart_id=1,
            user_id=user_id,
            session_id=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Mock repository methods
        service.cart_repo.get_cart_by_user = AsyncMock(return_value=None)
        service.cart_repo.create_cart = AsyncMock(return_value=new_cart)
        
        result = await service.get_or_create_cart(user_id=user_id)
        
        assert result == new_cart
        service.cart_repo.get_cart_by_user.assert_called_once_with(user_id)
        service.cart_repo.create_cart.assert_called_once()

    async def test_get_or_create_cart_for_session_existing(self):
        """Test getting existing cart for session"""
        mock_session = Mock(spec=AsyncSession)
        service = CartService(mock_session)
        
        session_id = "session_123"
        existing_cart = Cart(
            cart_id=2,
            user_id=None,
            session_id=session_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Mock repository method
        service.cart_repo.get_cart_by_session = AsyncMock(return_value=existing_cart)
        
        result = await service.get_or_create_cart(session_id=session_id)
        
        assert result == existing_cart
        service.cart_repo.get_cart_by_session.assert_called_once_with(session_id)

    async def test_get_or_create_cart_for_session_new(self):
        """Test creating new cart for session"""
        mock_session = Mock(spec=AsyncSession)
        service = CartService(mock_session)
        
        session_id = "session_123"
        new_cart = Cart(
            cart_id=2,
            user_id=None,
            session_id=session_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Mock repository methods
        service.cart_repo.get_cart_by_session = AsyncMock(return_value=None)
        service.cart_repo.create_cart = AsyncMock(return_value=new_cart)
        
        result = await service.get_or_create_cart(session_id=session_id)
        
        assert result == new_cart
        service.cart_repo.get_cart_by_session.assert_called_once_with(session_id)
        service.cart_repo.create_cart.assert_called_once()


class TestAddToCart:
    """Test adding items to cart functionality"""

    async def test_add_to_cart_new_item_success(self):
        """Test successfully adding new item to cart"""
        mock_session = Mock(spec=AsyncSession)
        mock_session.add = Mock()
        mock_session.commit = AsyncMock()
        
        service = CartService(mock_session)
        
        # Setup test data
        user_id = uuid.uuid4()
        product_id = 1
        quantity = 2
        
        product = Product(
            product_id=product_id,
            name="Test Product",
            sku="TEST-001",
            unit_price=Decimal("29.99"),
            status=ProductStatus.ACTIVE
        )
        
        cart = Cart(cart_id=1, user_id=user_id)
        cart_read = CartRead(
            cart_id=1,
            user_id=user_id,
            session_id=None,
            items=[],
            total_amount=Decimal("59.98"),
            item_count=2,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        request = AddToCartRequest(product_id=product_id, quantity=quantity)
        
        # Mock repository methods
        service.product_repo.get_by_id = AsyncMock(return_value=product)
        service.cart_repo.get_cart_by_user = AsyncMock(return_value=cart)
        service.cart_repo.get_cart_item = AsyncMock(return_value=None)  # No existing item
        service.cart_repo.add_cart_item = AsyncMock()
        
        with patch.object(service, 'get_cart_details', return_value=cart_read):
            result = await service.add_to_cart(request, user_id=user_id)
        
        assert result == cart_read
        service.product_repo.get_by_id.assert_called_once_with(product_id)
        service.cart_repo.get_cart_item.assert_called_once_with(cart.cart_id, product_id)
        service.cart_repo.add_cart_item.assert_called_once()

    async def test_add_to_cart_existing_item_updates_quantity(self):
        """Test adding to existing cart item updates quantity"""
        mock_session = Mock(spec=AsyncSession)
        mock_session.add = Mock()
        mock_session.commit = AsyncMock()
        
        service = CartService(mock_session)
        
        # Setup test data
        user_id = uuid.uuid4()
        product_id = 1
        additional_quantity = 2
        existing_quantity = 3
        
        product = Product(
            product_id=product_id,
            name="Test Product",
            sku="TEST-001",
            unit_price=Decimal("29.99"),
            status=ProductStatus.ACTIVE
        )
        
        cart = Cart(cart_id=1, user_id=user_id)
        existing_item = CartItem(
            cart_id=cart.cart_id,
            product_id=product_id,
            quantity=existing_quantity
        )
        
        cart_read = CartRead(
            cart_id=1,
            user_id=user_id,
            session_id=None,
            items=[],
            total_amount=Decimal("149.95"),
            item_count=5,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        request = AddToCartRequest(product_id=product_id, quantity=additional_quantity)
        
        # Mock repository methods
        service.product_repo.get_by_id = AsyncMock(return_value=product)
        service.cart_repo.get_cart_by_user = AsyncMock(return_value=cart)
        service.cart_repo.get_cart_item = AsyncMock(return_value=existing_item)
        service.cart_repo.update_cart_item = AsyncMock()
        
        with patch.object(service, 'get_cart_details', return_value=cart_read):
            result = await service.add_to_cart(request, user_id=user_id)
        
        assert result == cart_read
        assert existing_item.quantity == existing_quantity + additional_quantity
        service.cart_repo.update_cart_item.assert_called_once_with(existing_item)

    async def test_add_to_cart_product_not_found(self):
        """Test adding non-existent product to cart raises error"""
        mock_session = Mock(spec=AsyncSession)
        service = CartService(mock_session)
        
        user_id = uuid.uuid4()
        product_id = 999  # Non-existent product
        request = AddToCartRequest(product_id=product_id, quantity=1)
        
        # Mock repository method
        service.product_repo.get_by_id = AsyncMock(return_value=None)
        
        with pytest.raises(HTTPException) as exc_info:
            await service.add_to_cart(request, user_id=user_id)
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Product not found" in exc_info.value.detail

    async def test_add_to_cart_inactive_product(self):
        """Test adding inactive product to cart raises error"""
        mock_session = Mock(spec=AsyncSession)
        service = CartService(mock_session)
        
        user_id = uuid.uuid4()
        product_id = 1
        
        inactive_product = Product(
            product_id=product_id,
            name="Inactive Product",
            sku="INACTIVE-001",
            unit_price=Decimal("29.99"),
            status=ProductStatus.DISCONTINUED
        )
        
        request = AddToCartRequest(product_id=product_id, quantity=1)
        
        # Mock repository method
        service.product_repo.get_by_id = AsyncMock(return_value=inactive_product)
        
        with pytest.raises(HTTPException) as exc_info:
            await service.add_to_cart(request, user_id=user_id)
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Product is not available" in exc_info.value.detail


class TestUpdateCartItem:
    """Test updating cart item functionality"""

    async def test_update_cart_item_success(self):
        """Test successfully updating cart item quantity"""
        mock_session = Mock(spec=AsyncSession)
        mock_session.add = Mock()
        mock_session.commit = AsyncMock()
        
        service = CartService(mock_session)
        
        user_id = uuid.uuid4()
        product_id = 1
        new_quantity = 5
        
        cart = Cart(cart_id=1, user_id=user_id)
        cart_item = CartItem(cart_id=cart.cart_id, product_id=product_id, quantity=2)
        
        cart_read = CartRead(
            cart_id=1,
            user_id=user_id,
            session_id=None,
            items=[],
            total_amount=Decimal("149.95"),
            item_count=5,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        request = UpdateCartItemRequest(quantity=new_quantity)
        
        # Mock repository methods
        service.cart_repo.get_cart_by_user = AsyncMock(return_value=cart)
        service.cart_repo.get_cart_item = AsyncMock(return_value=cart_item)
        service.cart_repo.update_cart_item = AsyncMock()
        
        with patch.object(service, 'get_cart_details', return_value=cart_read):
            result = await service.update_cart_item(product_id, request, user_id=user_id)
        
        assert result == cart_read
        assert cart_item.quantity == new_quantity
        service.cart_repo.update_cart_item.assert_called_once_with(cart_item)

    async def test_update_cart_item_not_found(self):
        """Test updating non-existent cart item raises error"""
        mock_session = Mock(spec=AsyncSession)
        service = CartService(mock_session)
        
        user_id = uuid.uuid4()
        product_id = 999
        
        cart = Cart(cart_id=1, user_id=user_id)
        request = UpdateCartItemRequest(quantity=3)
        
        # Mock repository methods
        service.cart_repo.get_cart_by_user = AsyncMock(return_value=cart)
        service.cart_repo.get_cart_item = AsyncMock(return_value=None)
        
        with pytest.raises(HTTPException) as exc_info:
            await service.update_cart_item(product_id, request, user_id=user_id)
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Item not found in cart" in exc_info.value.detail


class TestRemoveFromCart:
    """Test removing items from cart functionality"""

    async def test_remove_from_cart_success(self):
        """Test successfully removing item from cart"""
        mock_session = Mock(spec=AsyncSession)
        mock_session.add = Mock()
        mock_session.commit = AsyncMock()
        
        service = CartService(mock_session)
        
        user_id = uuid.uuid4()
        product_id = 1
        
        cart = Cart(cart_id=1, user_id=user_id)
        cart_item = CartItem(cart_id=cart.cart_id, product_id=product_id, quantity=2)
        
        cart_read = CartRead(
            cart_id=1,
            user_id=user_id,
            session_id=None,
            items=[],
            total_amount=Decimal("0.00"),
            item_count=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Mock repository methods
        service.cart_repo.get_cart_by_user = AsyncMock(return_value=cart)
        service.cart_repo.get_cart_item = AsyncMock(return_value=cart_item)
        service.cart_repo.remove_cart_item = AsyncMock()
        
        with patch.object(service, 'get_cart_details', return_value=cart_read):
            result = await service.remove_from_cart(product_id, user_id=user_id)
        
        assert result == cart_read
        service.cart_repo.remove_cart_item.assert_called_once_with(cart_item)

    async def test_remove_from_cart_item_not_found(self):
        """Test removing non-existent cart item raises error"""
        mock_session = Mock(spec=AsyncSession)
        service = CartService(mock_session)
        
        user_id = uuid.uuid4()
        product_id = 999
        
        cart = Cart(cart_id=1, user_id=user_id)
        
        # Mock repository methods
        service.cart_repo.get_cart_by_user = AsyncMock(return_value=cart)
        service.cart_repo.get_cart_item = AsyncMock(return_value=None)
        
        with pytest.raises(HTTPException) as exc_info:
            await service.remove_from_cart(product_id, user_id=user_id)
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Item not found in cart" in exc_info.value.detail


class TestCartOperations:
    """Test cart-level operations"""

    async def test_get_cart_success(self):
        """Test getting cart details"""
        mock_session = Mock(spec=AsyncSession)
        service = CartService(mock_session)
        
        user_id = uuid.uuid4()
        cart = Cart(cart_id=1, user_id=user_id)
        
        cart_read = CartRead(
            cart_id=1,
            user_id=user_id,
            session_id=None,
            items=[],
            total_amount=Decimal("59.98"),
            item_count=2,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Mock repository method
        service.cart_repo.get_cart_by_user = AsyncMock(return_value=cart)
        
        with patch.object(service, 'get_cart_details', return_value=cart_read):
            result = await service.get_cart(user_id=user_id)
        
        assert result == cart_read

    async def test_clear_cart_success(self):
        """Test clearing cart successfully"""
        mock_session = Mock(spec=AsyncSession)
        service = CartService(mock_session)
        
        user_id = uuid.uuid4()
        cart = Cart(cart_id=1, user_id=user_id)
        
        # Mock repository methods
        service.cart_repo.get_cart_by_user = AsyncMock(return_value=cart)
        service.cart_repo.clear_cart = AsyncMock()
        
        await service.clear_cart(user_id=user_id)
        
        service.cart_repo.clear_cart.assert_called_once_with(cart.cart_id)


class TestCartDetails:
    """Test cart details calculation"""

    async def test_get_cart_details_with_items(self):
        """Test getting detailed cart information with items"""
        mock_session = Mock(spec=AsyncSession)
        mock_session.get = AsyncMock()
        
        service = CartService(mock_session)
        
        cart_id = 1
        cart = Cart(
            cart_id=cart_id,
            user_id=uuid.uuid4(),
            session_id=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Mock cart items with products
        class MockCartItemWithProduct:
            def __init__(self, product_id, quantity, product):
                self.product_id = product_id
                self.quantity = quantity
                self.product = product
        
        product1 = Product(
            product_id=1,
            name="Product 1",
            sku="PROD-001",
            unit_price=Decimal("29.99")
        )
        product2 = Product(
            product_id=2,
            name="Product 2",
            sku="PROD-002",
            unit_price=Decimal("19.99")
        )
        
        items = [
            MockCartItemWithProduct(1, 2, product1),
            MockCartItemWithProduct(2, 1, product2)
        ]
        
        # Mock repository method and session.get
        service.cart_repo.get_cart_items_with_products = AsyncMock(return_value=items)
        mock_session.get.return_value = cart
        
        result = await service.get_cart_details(cart_id)
        
        assert result.cart_id == cart_id
        assert result.user_id == cart.user_id
        assert len(result.items) == 2
        assert result.total_amount == Decimal("79.97")  # (29.99 * 2) + (19.99 * 1)
        assert result.item_count == 3  # 2 + 1

    async def test_get_cart_details_empty_cart(self):
        """Test getting details for empty cart"""
        mock_session = Mock(spec=AsyncSession)
        mock_session.get = AsyncMock()
        
        service = CartService(mock_session)
        
        cart_id = 1
        cart = Cart(
            cart_id=cart_id,
            user_id=uuid.uuid4(),
            session_id=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Mock repository method and session.get
        service.cart_repo.get_cart_items_with_products = AsyncMock(return_value=[])
        mock_session.get.return_value = cart
        
        result = await service.get_cart_details(cart_id)
        
        assert result.cart_id == cart_id
        assert result.user_id == cart.user_id
        assert len(result.items) == 0
        assert result.total_amount == Decimal("0.00")
        assert result.item_count == 0


class TestCartSessionHandling:
    """Test cart session handling functionality"""

    async def test_session_cart_creation(self):
        """Test creating cart for session ID"""
        mock_session = Mock(spec=AsyncSession)
        service = CartService(mock_session)
        
        session_id = "session_abc123"
        new_cart = Cart(
            cart_id=1,
            user_id=None,
            session_id=session_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Mock repository methods
        service.cart_repo.get_cart_by_session = AsyncMock(return_value=None)
        service.cart_repo.create_cart = AsyncMock(return_value=new_cart)
        
        result = await service.get_or_create_cart(session_id=session_id)
        
        assert result == new_cart
        assert result.session_id == session_id
        assert result.user_id is None

    async def test_session_cart_add_item(self):
        """Test adding item to session cart"""
        mock_session = Mock(spec=AsyncSession)
        mock_session.add = Mock()
        mock_session.commit = AsyncMock()
        
        service = CartService(mock_session)
        
        session_id = "session_abc123"
        product_id = 1
        
        product = Product(
            product_id=product_id,
            name="Test Product",
            sku="TEST-001",
            unit_price=Decimal("29.99"),
            status=ProductStatus.ACTIVE
        )
        
        cart = Cart(cart_id=1, user_id=None, session_id=session_id)
        cart_read = CartRead(
            cart_id=1,
            user_id=None,
            session_id=session_id,
            items=[],
            total_amount=Decimal("29.99"),
            item_count=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        request = AddToCartRequest(product_id=product_id, quantity=1)
        
        # Mock repository methods
        service.product_repo.get_by_id = AsyncMock(return_value=product)
        service.cart_repo.get_cart_by_session = AsyncMock(return_value=cart)
        service.cart_repo.get_cart_item = AsyncMock(return_value=None)
        service.cart_repo.add_cart_item = AsyncMock()
        
        with patch.object(service, 'get_cart_details', return_value=cart_read):
            result = await service.add_to_cart(request, session_id=session_id)
        
        assert result == cart_read
        assert result.session_id == session_id


class TestEdgeCases:
    """Test edge cases and error conditions"""

    async def test_add_to_cart_zero_quantity(self):
        """Test adding zero quantity to cart (should be validated by schema)"""
        # This would be caught by Pydantic validation before reaching the service
        with pytest.raises(ValueError):
            AddToCartRequest(product_id=1, quantity=0)

    async def test_update_cart_item_zero_quantity(self):
        """Test updating cart item with zero quantity (should be validated by schema)"""
        # This would be caught by Pydantic validation before reaching the service
        with pytest.raises(ValueError):
            UpdateCartItemRequest(quantity=0)

    async def test_get_cart_details_decimal_precision(self):
        """Test cart details calculation with high decimal precision"""
        mock_session = Mock(spec=AsyncSession)
        mock_session.get = AsyncMock()
        
        service = CartService(mock_session)
        
        cart_id = 1
        cart = Cart(cart_id=cart_id, user_id=uuid.uuid4())
        
        # Mock cart item with high precision price
        class MockCartItemWithProduct:
            def __init__(self, product_id, quantity, product):
                self.product_id = product_id
                self.quantity = quantity
                self.product = product
        
        product = Product(
            product_id=1,
            name="High Precision Product",
            sku="PREC-001",
            unit_price=Decimal("33.333")
        )
        
        items = [MockCartItemWithProduct(1, 3, product)]
        
        # Mock repository method and session.get
        service.cart_repo.get_cart_items_with_products = AsyncMock(return_value=items)
        mock_session.get.return_value = cart
        
        result = await service.get_cart_details(cart_id)
        
        # 33.333 * 3 = 99.999
        assert result.total_amount == Decimal("99.999")
        assert result.item_count == 3

    async def test_cart_operations_without_user_or_session(self):
        """Test cart operations when neither user_id nor session_id provided"""
        mock_session = Mock(spec=AsyncSession)
        service = CartService(mock_session)
        
        # This should create a cart but may not be practical in real usage
        # The service should handle this gracefully
        
        # Mock repository methods
        service.cart_repo.get_cart_by_user = AsyncMock(return_value=None)
        service.cart_repo.get_cart_by_session = AsyncMock(return_value=None)
        
        new_cart = Cart(
            cart_id=1,
            user_id=None,
            session_id=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        service.cart_repo.create_cart = AsyncMock(return_value=new_cart)
        
        result = await service.get_or_create_cart()
        
        assert result == new_cart
        assert result.user_id is None
        assert result.session_id is None


class TestCartIntegrationScenarios:
    """Test realistic cart usage scenarios"""

    async def test_typical_shopping_flow(self):
        """Test a typical shopping flow: add items, update quantities, remove item"""
        mock_session = Mock(spec=AsyncSession)
        mock_session.add = Mock()
        mock_session.commit = AsyncMock()
        
        service = CartService(mock_session)
        
        user_id = uuid.uuid4()
        
        # Setup products
        product1 = Product(product_id=1, name="Product 1", sku="PROD-001", unit_price=Decimal("29.99"), status=ProductStatus.ACTIVE)
        product2 = Product(product_id=2, name="Product 2", sku="PROD-002", unit_price=Decimal("19.99"), status=ProductStatus.ACTIVE)
        
        cart = Cart(cart_id=1, user_id=user_id)
        
        # Mock repository methods
        service.product_repo.get_by_id = AsyncMock(side_effect=lambda pid: product1 if pid == 1 else product2)
        service.cart_repo.get_cart_by_user = AsyncMock(return_value=cart)
        service.cart_repo.get_cart_item = AsyncMock(return_value=None)  # No existing items initially
        service.cart_repo.add_cart_item = AsyncMock()
        service.cart_repo.update_cart_item = AsyncMock()
        service.cart_repo.remove_cart_item = AsyncMock()
        
        # Mock get_cart_details to return appropriate responses
        cart_reads = [
            CartRead(cart_id=1, user_id=user_id, session_id=None, items=[], total_amount=Decimal("29.99"), item_count=1, created_at=datetime.utcnow(), updated_at=datetime.utcnow()),
            CartRead(cart_id=1, user_id=user_id, session_id=None, items=[], total_amount=Decimal("49.98"), item_count=2, created_at=datetime.utcnow(), updated_at=datetime.utcnow()),
            CartRead(cart_id=1, user_id=user_id, session_id=None, items=[], total_amount=Decimal("89.97"), item_count=3, created_at=datetime.utcnow(), updated_at=datetime.utcnow()),
            CartRead(cart_id=1, user_id=user_id, session_id=None, items=[], total_amount=Decimal("19.99"), item_count=1, created_at=datetime.utcnow(), updated_at=datetime.utcnow())
        ]
        
        # 1. Add first product
        with patch.object(service, 'get_cart_details', return_value=cart_reads[0]):
            result1 = await service.add_to_cart(AddToCartRequest(product_id=1, quantity=1), user_id=user_id)
            assert result1.total_amount == Decimal("29.99")
        
        # 2. Add second product
        with patch.object(service, 'get_cart_details', return_value=cart_reads[1]):
            result2 = await service.add_to_cart(AddToCartRequest(product_id=2, quantity=1), user_id=user_id)
            assert result2.total_amount == Decimal("49.98")
        
        # 3. Update first product quantity
        item1 = CartItem(cart_id=1, product_id=1, quantity=1)
        service.cart_repo.get_cart_item = AsyncMock(return_value=item1)
        
        with patch.object(service, 'get_cart_details', return_value=cart_reads[2]):
            result3 = await service.update_cart_item(1, UpdateCartItemRequest(quantity=3), user_id=user_id)
            assert result3.total_amount == Decimal("89.97")
        
        # 4. Remove first product
        with patch.object(service, 'get_cart_details', return_value=cart_reads[3]):
            result4 = await service.remove_from_cart(1, user_id=user_id)
            assert result4.total_amount == Decimal("19.99")