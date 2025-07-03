"""
Unit tests for Shipping Service.
Tests shipping calculations, delivery tracking, and logistics integration.
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from app.services.shipping_service import ShippingService
from app.tests.fixtures.factories import OrderFactory, ProductFactory


class TestShippingService:
    """Test cases for ShippingService."""

    @pytest.fixture
    def mock_repository(self) -> Mock:
        """Create a mock repository."""
        return Mock()

    @pytest.fixture
    def service(self, mock_repository: Mock) -> ShippingService:
        """Create a ShippingService instance with mocked dependencies."""
        return ShippingService(repository=mock_repository)

    def test_calculate_shipping_cost_standard(self, service: ShippingService):
        """Test standard shipping cost calculation."""
        order_data = {
            "total_weight": 2.5,  # kg
            "destination": {
                "state": "Ciudad de México",
                "postal_code": "01000"
            },
            "items_count": 3
        }
        
        cost = service.calculate_shipping_cost(order_data, shipping_method="standard")
        
        assert isinstance(cost, Decimal)
        assert cost > 0
        assert cost < 200  # Reasonable shipping cost for Mexico

    def test_calculate_shipping_cost_express(self, service: ShippingService):
        """Test express shipping cost calculation."""
        order_data = {
            "total_weight": 1.0,
            "destination": {
                "state": "Jalisco", 
                "postal_code": "44100"
            },
            "items_count": 2
        }
        
        standard_cost = service.calculate_shipping_cost(order_data, "standard")
        express_cost = service.calculate_shipping_cost(order_data, "express")
        
        assert express_cost > standard_cost
        assert express_cost <= standard_cost * 2  # Express should be reasonable multiple

    def test_calculate_shipping_cost_free_threshold(self, service: ShippingService):
        """Test free shipping for orders above threshold."""
        order_data = {
            "total_amount": Decimal("1000.00"),  # Above free shipping threshold
            "total_weight": 1.0,
            "destination": {
                "state": "Nuevo León",
                "postal_code": "64000"
            },
            "items_count": 1
        }
        
        cost = service.calculate_shipping_cost(order_data, "standard")
        
        assert cost == Decimal("0.00")

    def test_estimate_delivery_date_standard(self, service: ShippingService):
        """Test delivery date estimation for standard shipping."""
        destination = {
            "state": "Ciudad de México",
            "postal_code": "01000"
        }
        
        delivery_date = service.estimate_delivery_date(destination, "standard")
        
        assert isinstance(delivery_date, datetime)
        assert delivery_date > datetime.now()
        assert delivery_date <= datetime.now() + timedelta(days=7)

    def test_estimate_delivery_date_express(self, service: ShippingService):
        """Test delivery date estimation for express shipping."""
        destination = {
            "state": "Jalisco",
            "postal_code": "44100"
        }
        
        standard_delivery = service.estimate_delivery_date(destination, "standard")
        express_delivery = service.estimate_delivery_date(destination, "express")
        
        assert express_delivery < standard_delivery

    def test_create_shipping_label(self, service: ShippingService, mock_repository: Mock):
        """Test shipping label creation."""
        order = OrderFactory()
        
        with patch('app.services.shipping_service.ShippingService._call_shipping_api') as mock_api:
            mock_api.return_value = {
                "tracking_number": "MX123456789",
                "label_url": "https://shipping.com/label/123",
                "estimated_delivery": "2024-01-15"
            }
            
            label_data = service.create_shipping_label(order)
            
            assert "tracking_number" in label_data
            assert "label_url" in label_data
            assert label_data["tracking_number"].startswith("MX")

    def test_track_shipment(self, service: ShippingService):
        """Test shipment tracking."""
        tracking_number = "MX123456789"
        
        with patch('app.services.shipping_service.ShippingService._call_tracking_api') as mock_api:
            mock_api.return_value = {
                "status": "in_transit",
                "location": "Centro de distribución CDMX",
                "estimated_delivery": "2024-01-15T18:00:00",
                "tracking_events": [
                    {
                        "timestamp": "2024-01-10T10:00:00",
                        "status": "picked_up",
                        "location": "Almacén"
                    },
                    {
                        "timestamp": "2024-01-12T14:30:00", 
                        "status": "in_transit",
                        "location": "Centro de distribución CDMX"
                    }
                ]
            }
            
            tracking_info = service.track_shipment(tracking_number)
            
            assert tracking_info["status"] == "in_transit"
            assert len(tracking_info["tracking_events"]) == 2

    def test_validate_shipping_address(self, service: ShippingService):
        """Test shipping address validation."""
        valid_address = {
            "street": "Av. Reforma 123",
            "city": "Ciudad de México",
            "state": "Ciudad de México",
            "postal_code": "01000",
            "country": "Mexico"
        }
        
        is_valid = service.validate_shipping_address(valid_address)
        assert is_valid is True

    def test_validate_shipping_address_invalid(self, service: ShippingService):
        """Test invalid shipping address validation."""
        invalid_address = {
            "street": "Test St",
            "city": "Invalid City",
            "state": "Invalid State",
            "postal_code": "99999",
            "country": "Mexico"
        }
        
        is_valid = service.validate_shipping_address(invalid_address)
        assert is_valid is False

    def test_get_available_shipping_methods(self, service: ShippingService):
        """Test getting available shipping methods for location."""
        destination = {
            "state": "Ciudad de México",
            "postal_code": "01000"
        }
        
        methods = service.get_available_shipping_methods(destination)
        
        assert isinstance(methods, list)
        assert len(methods) > 0
        assert all("id" in method for method in methods)
        assert all("name" in method for method in methods)
        assert all("estimated_days" in method for method in methods)

    def test_calculate_dimensional_weight(self, service: ShippingService):
        """Test dimensional weight calculation."""
        package_dimensions = {
            "length": 30,  # cm
            "width": 20,   # cm
            "height": 15,  # cm
            "actual_weight": 1.5  # kg
        }
        
        dimensional_weight = service.calculate_dimensional_weight(package_dimensions)
        
        assert isinstance(dimensional_weight, Decimal)
        assert dimensional_weight >= Decimal("1.5")  # Should be at least actual weight

    def test_shipping_cost_by_zone(self, service: ShippingService):
        """Test shipping cost calculation by geographic zone."""
        # Zone 1: Mexico City (local)
        local_order = {
            "total_weight": 1.0,
            "destination": {"state": "Ciudad de México", "postal_code": "01000"},
            "items_count": 1
        }
        
        # Zone 3: Remote area
        remote_order = {
            "total_weight": 1.0,
            "destination": {"state": "Yucatán", "postal_code": "97000"},
            "items_count": 1
        }
        
        local_cost = service.calculate_shipping_cost(local_order, "standard")
        remote_cost = service.calculate_shipping_cost(remote_order, "standard")
        
        assert remote_cost >= local_cost

    def test_bulk_shipping_discount(self, service: ShippingService):
        """Test bulk shipping discount for multiple items."""
        small_order = {
            "total_weight": 0.5,
            "destination": {"state": "Ciudad de México", "postal_code": "01000"},
            "items_count": 1
        }
        
        bulk_order = {
            "total_weight": 2.5,  # 5x weight
            "destination": {"state": "Ciudad de México", "postal_code": "01000"},
            "items_count": 5     # 5x items
        }
        
        small_cost = service.calculate_shipping_cost(small_order, "standard")
        bulk_cost = service.calculate_shipping_cost(bulk_order, "standard")
        
        # Bulk should have better rate per item
        assert bulk_cost < (small_cost * 5)

    def test_shipping_restrictions(self, service: ShippingService):
        """Test shipping restrictions for certain products/locations."""
        restricted_product = ProductFactory(category="supplements", weight=5.0)
        
        restrictions = service.check_shipping_restrictions(
            product=restricted_product,
            destination={"state": "International", "country": "US"}
        )
        
        assert isinstance(restrictions, dict)
        assert "allowed" in restrictions

    def test_shipping_insurance_calculation(self, service: ShippingService):
        """Test shipping insurance cost calculation."""
        high_value_order = {
            "total_amount": Decimal("5000.00"),
            "total_weight": 1.0,
            "destination": {"state": "Ciudad de México", "postal_code": "01000"},
            "items_count": 1
        }
        
        insurance_cost = service.calculate_shipping_insurance(high_value_order)
        
        assert isinstance(insurance_cost, Decimal)
        assert insurance_cost > 0
        assert insurance_cost < high_value_order["total_amount"] * Decimal("0.05")  # Max 5%

    def test_delivery_confirmation_required(self, service: ShippingService):
        """Test delivery confirmation requirements."""
        high_value_order = {
            "total_amount": Decimal("2000.00"),
            "destination": {"state": "Ciudad de México", "postal_code": "01000"}
        }
        
        requires_confirmation = service.requires_delivery_confirmation(high_value_order)
        
        assert isinstance(requires_confirmation, bool)
        assert requires_confirmation is True  # High value should require confirmation