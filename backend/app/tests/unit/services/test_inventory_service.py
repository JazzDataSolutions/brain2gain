"""
Unit tests for InventoryService.
Tests for stock management, inventory tracking, and availability checks.
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, AsyncMock
from sqlmodel import Session

from app.services.inventory_service import InventoryService
from app.models import Product, Stock
from app.tests.fixtures.factories import ProductFactory, StockFactory


class TestInventoryService:
    """Test suite for InventoryService."""

    @pytest.fixture
    def mock_session(self):
        """Mock database session."""
        return Mock(spec=Session)

    @pytest.fixture
    def service(self, mock_session):
        """InventoryService instance with mocked dependencies."""
        return InventoryService(session=mock_session)

    def test_check_stock_availability_in_stock(self, service, mock_session):
        """Test checking stock availability when product is in stock."""
        # Setup
        product_id = 1
        quantity = 5
        mock_stock = StockFactory(product_id=product_id, quantity=10)
        mock_session.exec.return_value.first.return_value = mock_stock

        # Execute
        result = service.check_stock_availability(product_id, quantity)

        # Assert
        assert result is True
        mock_session.exec.assert_called_once()

    def test_check_stock_availability_insufficient_stock(self, service, mock_session):
        """Test checking stock availability when stock is insufficient."""
        # Setup
        product_id = 1
        quantity = 15
        mock_stock = StockFactory(product_id=product_id, quantity=10)
        mock_session.exec.return_value.first.return_value = mock_stock

        # Execute
        result = service.check_stock_availability(product_id, quantity)

        # Assert
        assert result is False

    def test_check_stock_availability_no_stock_record(self, service, mock_session):
        """Test checking stock availability when no stock record exists."""
        # Setup
        product_id = 1
        quantity = 5
        mock_session.exec.return_value.first.return_value = None

        # Execute
        result = service.check_stock_availability(product_id, quantity)

        # Assert
        assert result is False

    def test_reserve_stock_success(self, service, mock_session):
        """Test successful stock reservation."""
        # Setup
        product_id = 1
        quantity = 5
        mock_stock = StockFactory(
            product_id=product_id, 
            quantity=10, 
            reserved_quantity=2
        )
        mock_session.exec.return_value.first.return_value = mock_stock

        # Execute
        result = service.reserve_stock(product_id, quantity)

        # Assert
        assert result is True
        assert mock_stock.reserved_quantity == 7  # 2 + 5
        mock_session.add.assert_called_once_with(mock_stock)
        mock_session.commit.assert_called_once()

    def test_reserve_stock_insufficient_available(self, service, mock_session):
        """Test stock reservation when insufficient stock available."""
        # Setup
        product_id = 1
        quantity = 15
        mock_stock = StockFactory(
            product_id=product_id, 
            quantity=10, 
            reserved_quantity=2
        )  # Available: 10 - 2 = 8, but requesting 15
        mock_session.exec.return_value.first.return_value = mock_stock

        # Execute
        result = service.reserve_stock(product_id, quantity)

        # Assert
        assert result is False
        assert mock_stock.reserved_quantity == 2  # Unchanged
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()

    def test_release_stock_reservation(self, service, mock_session):
        """Test releasing stock reservation."""
        # Setup
        product_id = 1
        quantity = 3
        mock_stock = StockFactory(
            product_id=product_id, 
            quantity=10, 
            reserved_quantity=5
        )
        mock_session.exec.return_value.first.return_value = mock_stock

        # Execute
        result = service.release_stock_reservation(product_id, quantity)

        # Assert
        assert result is True
        assert mock_stock.reserved_quantity == 2  # 5 - 3
        mock_session.add.assert_called_once_with(mock_stock)
        mock_session.commit.assert_called_once()

    def test_update_stock_levels(self, service, mock_session):
        """Test updating stock levels."""
        # Setup
        product_id = 1
        new_quantity = 20
        mock_stock = StockFactory(product_id=product_id, quantity=10)
        mock_session.exec.return_value.first.return_value = mock_stock

        # Execute
        result = service.update_stock_levels(product_id, new_quantity)

        # Assert
        assert result is True
        assert mock_stock.quantity == new_quantity
        mock_session.add.assert_called_once_with(mock_stock)
        mock_session.commit.assert_called_once()

    def test_get_low_stock_products(self, service, mock_session):
        """Test getting products with low stock."""
        # Setup
        low_stock_products = [
            StockFactory(product_id=1, quantity=5, min_stock_level=10),
            StockFactory(product_id=2, quantity=2, min_stock_level=15)
        ]
        mock_session.exec.return_value.all.return_value = low_stock_products

        # Execute
        result = service.get_low_stock_products()

        # Assert
        assert len(result) == 2
        assert result == low_stock_products
        mock_session.exec.assert_called_once()

    def test_calculate_stock_value(self, service, mock_session):
        """Test calculating total stock value."""
        # Setup
        products_with_stock = [
            (ProductFactory(unit_price=Decimal("50.00")), StockFactory(quantity=10)),
            (ProductFactory(unit_price=Decimal("25.00")), StockFactory(quantity=20)),
        ]
        mock_session.exec.return_value.all.return_value = products_with_stock

        # Execute
        result = service.calculate_stock_value()

        # Assert
        expected_value = (Decimal("50.00") * 10) + (Decimal("25.00") * 20)
        assert result == expected_value

    def test_validate_stock_levels(self, service, mock_session):
        """Test validating stock levels consistency."""
        # Setup
        valid_stocks = [
            StockFactory(quantity=10, reserved_quantity=5),
            StockFactory(quantity=20, reserved_quantity=8)
        ]
        mock_session.exec.return_value.all.return_value = valid_stocks

        # Execute
        result = service.validate_stock_levels()

        # Assert
        assert result is True

    def test_validate_stock_levels_invalid(self, service, mock_session):
        """Test validating stock levels with invalid data."""
        # Setup - reserved quantity exceeds total quantity
        invalid_stocks = [
            StockFactory(quantity=10, reserved_quantity=15)  # Invalid
        ]
        mock_session.exec.return_value.all.return_value = invalid_stocks

        # Execute
        result = service.validate_stock_levels()

        # Assert
        assert result is False