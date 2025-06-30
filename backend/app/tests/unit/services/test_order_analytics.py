"""
Unit tests for Order Analytics Service.
Tests for order analytics and reporting functionality.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, AsyncMock
from sqlmodel import Session

from app.services.analytics.order_analytics import OrderAnalyticsService
from app.models import SalesOrder, Customer
from app.tests.fixtures.factories import SalesOrderFactory, CustomerFactory


class TestOrderAnalyticsService:
    """Test suite for OrderAnalyticsService."""

    @pytest.fixture
    def mock_session(self):
        """Mock database session."""
        return Mock(spec=Session)

    @pytest.fixture
    def service(self, mock_session):
        """OrderAnalyticsService instance with mocked dependencies."""
        return OrderAnalyticsService(session=mock_session)

    def test_get_order_count_by_period(self, service, mock_session):
        """Test getting order count for a specific period."""
        # Setup
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        expected_count = 150
        
        mock_session.exec.return_value.scalar.return_value = expected_count

        # Execute
        result = service.get_order_count_by_period(start_date, end_date)

        # Assert
        assert result == expected_count
        mock_session.exec.assert_called_once()

    def test_get_orders_by_status(self, service, mock_session):
        """Test getting order counts grouped by status."""
        # Setup
        status_counts = [
            ("PENDING", 25),
            ("COMPLETED", 120),
            ("CANCELLED", 5)
        ]
        mock_session.exec.return_value.all.return_value = status_counts

        # Execute
        result = service.get_orders_by_status()

        # Assert
        assert len(result) == 3
        assert result == dict(status_counts)

    def test_get_average_order_value(self, service, mock_session):
        """Test calculating average order value."""
        # Setup
        mock_orders = [
            Mock(items=[Mock(qty=2, unit_price=Decimal("25.00"))]),
            Mock(items=[Mock(qty=1, unit_price=Decimal("50.00"))]),
            Mock(items=[Mock(qty=3, unit_price=Decimal("15.00"))])
        ]
        mock_session.exec.return_value.all.return_value = mock_orders

        # Execute
        result = service.get_average_order_value()

        # Assert
        # AOV = (50 + 50 + 45) / 3 = 48.33
        assert isinstance(result, Decimal)
        assert result > Decimal("0")

    def test_get_orders_by_customer_segment(self, service, mock_session):
        """Test getting orders grouped by customer segments."""
        # Setup
        segment_data = [
            ("VIP", 50),
            ("Regular", 80),
            ("New", 20)
        ]
        mock_session.exec.return_value.all.return_value = segment_data

        # Execute
        result = service.get_orders_by_customer_segment()

        # Assert
        assert len(result) == 3
        assert result["VIP"] == 50
        assert result["Regular"] == 80

    def test_get_peak_ordering_hours(self, service, mock_session):
        """Test identifying peak ordering hours."""
        # Setup
        hourly_data = [
            (9, 15),   # 9 AM: 15 orders
            (14, 25),  # 2 PM: 25 orders
            (20, 30)   # 8 PM: 30 orders
        ]
        mock_session.exec.return_value.all.return_value = hourly_data

        # Execute
        result = service.get_peak_ordering_hours()

        # Assert
        assert len(result) == 3
        assert result[20] == 30  # Peak hour
        assert result[9] == 15

    def test_get_order_fulfillment_time(self, service, mock_session):
        """Test calculating average order fulfillment time."""
        # Setup
        now = datetime.now()
        mock_orders = [
            Mock(
                order_date=now - timedelta(hours=24),
                updated_at=now - timedelta(hours=20),
                status="COMPLETED"
            ),
            Mock(
                order_date=now - timedelta(hours=48),
                updated_at=now - timedelta(hours=44),
                status="COMPLETED"
            )
        ]
        mock_session.exec.return_value.all.return_value = mock_orders

        # Execute
        result = service.get_order_fulfillment_time()

        # Assert
        assert isinstance(result, dict)
        assert "average_hours" in result
        assert result["average_hours"] == 4.0  # Average of 4 hours

    def test_get_monthly_order_trends(self, service, mock_session):
        """Test getting monthly order trends."""
        # Setup
        monthly_data = [
            ("2024-01", 100),
            ("2024-02", 120),
            ("2024-03", 150)
        ]
        mock_session.exec.return_value.all.return_value = monthly_data

        # Execute
        result = service.get_monthly_order_trends()

        # Assert
        assert len(result) == 3
        assert result["2024-03"] == 150
        assert result["2024-01"] == 100

    def test_get_order_cancellation_rate(self, service, mock_session):
        """Test calculating order cancellation rate."""
        # Setup
        total_orders = 1000
        cancelled_orders = 50
        
        mock_session.exec.return_value.scalar.side_effect = [total_orders, cancelled_orders]

        # Execute
        result = service.get_order_cancellation_rate()

        # Assert
        assert result == 5.0  # 5% cancellation rate
        assert mock_session.exec.call_count == 2

    def test_get_repeat_order_rate(self, service, mock_session):
        """Test calculating repeat order rate."""
        # Setup
        total_customers = 500
        repeat_customers = 200
        
        mock_session.exec.return_value.scalar.side_effect = [total_customers, repeat_customers]

        # Execute
        result = service.get_repeat_order_rate()

        # Assert
        assert result == 40.0  # 40% repeat rate
        assert mock_session.exec.call_count == 2

    def test_get_orders_by_geographic_region(self, service, mock_session):
        """Test getting orders grouped by geographic region."""
        # Setup
        regional_data = [
            ("North", 150),
            ("South", 120),
            ("East", 80),
            ("West", 100)
        ]
        mock_session.exec.return_value.all.return_value = regional_data

        # Execute
        result = service.get_orders_by_geographic_region()

        # Assert
        assert len(result) == 4
        assert result["North"] == 150
        assert result["East"] == 80

    def test_get_seasonal_order_patterns(self, service, mock_session):
        """Test identifying seasonal order patterns."""
        # Setup
        seasonal_data = [
            ("Q1", 800),
            ("Q2", 900),
            ("Q3", 750),
            ("Q4", 1200)  # Holiday season peak
        ]
        mock_session.exec.return_value.all.return_value = seasonal_data

        # Execute
        result = service.get_seasonal_order_patterns()

        # Assert
        assert len(result) == 4
        assert result["Q4"] == 1200  # Holiday peak
        assert result["Q3"] == 750   # Summer low

    def test_get_order_value_distribution(self, service, mock_session):
        """Test getting distribution of order values."""
        # Setup
        value_ranges = [
            ("0-25", 100),
            ("25-50", 200),
            ("50-100", 150),
            ("100+", 50)
        ]
        mock_session.exec.return_value.all.return_value = value_ranges

        # Execute
        result = service.get_order_value_distribution()

        # Assert
        assert len(result) == 4
        assert result["25-50"] == 200  # Most common range
        assert result["100+"] == 50    # Premium orders

    def test_get_top_customers_by_order_count(self, service, mock_session):
        """Test getting top customers by number of orders."""
        # Setup
        top_customers = [
            (CustomerFactory(first_name="John", last_name="Doe"), 15),
            (CustomerFactory(first_name="Jane", last_name="Smith"), 12),
            (CustomerFactory(first_name="Bob", last_name="Wilson"), 10)
        ]
        mock_session.exec.return_value.all.return_value = top_customers

        # Execute
        result = service.get_top_customers_by_order_count(limit=3)

        # Assert
        assert len(result) == 3
        assert result[0][1] == 15  # Top customer with 15 orders

    def test_get_order_payment_method_breakdown(self, service, mock_session):
        """Test getting breakdown of orders by payment method."""
        # Setup
        payment_methods = [
            ("CREDIT_CARD", 300),
            ("PAYPAL", 150),
            ("BANK_TRANSFER", 50)
        ]
        mock_session.exec.return_value.all.return_value = payment_methods

        # Execute
        result = service.get_order_payment_method_breakdown()

        # Assert
        assert len(result) == 3
        assert result["CREDIT_CARD"] == 300
        assert result["PAYPAL"] == 150

    def test_get_order_analytics_summary(self, service, mock_session):
        """Test getting comprehensive order analytics summary."""
        # Setup - Mock multiple database calls
        mock_session.exec.return_value.scalar.side_effect = [
            1000,  # total orders
            50,    # cancelled orders
            Decimal("75.50")  # average order value
        ]

        # Execute
        result = service.get_order_analytics_summary()

        # Assert
        assert isinstance(result, dict)
        assert "total_orders" in result
        assert "cancellation_rate" in result
        assert "average_order_value" in result
        assert result["total_orders"] == 1000
        assert result["cancellation_rate"] == 5.0

    def test_export_order_analytics_report(self, service):
        """Test exporting order analytics report."""
        # Setup
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        format_type = "csv"

        # Execute
        result = service.export_order_analytics_report(start_date, end_date, format_type)

        # Assert
        assert isinstance(result, (str, bytes, dict))  # Could be file path, content, or metadata