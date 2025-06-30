"""
Unit tests for Revenue Analytics Service.
Tests for revenue tracking, financial metrics, and reporting functionality.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, AsyncMock
from sqlmodel import Session

from app.services.analytics.revenue_analytics import RevenueAnalyticsService
from app.models import SalesOrder, Transaction
from app.tests.fixtures.factories import SalesOrderFactory, TransactionFactory


class TestRevenueAnalyticsService:
    """Test suite for RevenueAnalyticsService."""

    @pytest.fixture
    def mock_session(self):
        """Mock database session."""
        return Mock(spec=Session)

    @pytest.fixture
    def service(self, mock_session):
        """RevenueAnalyticsService instance with mocked dependencies."""
        return RevenueAnalyticsService(session=mock_session)

    def test_get_total_revenue_by_period(self, service, mock_session):
        """Test getting total revenue for a specific period."""
        # Setup
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        expected_revenue = Decimal("15000.00")
        
        mock_session.exec.return_value.scalar.return_value = expected_revenue

        # Execute
        result = service.get_total_revenue_by_period(start_date, end_date)

        # Assert
        assert result == expected_revenue
        mock_session.exec.assert_called_once()

    def test_get_monthly_revenue_trends(self, service, mock_session):
        """Test getting monthly revenue trends."""
        # Setup
        monthly_data = [
            ("2024-01", Decimal("8000.00")),
            ("2024-02", Decimal("9500.00")),
            ("2024-03", Decimal("12000.00"))
        ]
        mock_session.exec.return_value.all.return_value = monthly_data

        # Execute
        result = service.get_monthly_revenue_trends()

        # Assert
        assert len(result) == 3
        assert result["2024-03"] == Decimal("12000.00")
        assert result["2024-01"] == Decimal("8000.00")

    def test_get_revenue_by_product_category(self, service, mock_session):
        """Test getting revenue breakdown by product category."""
        # Setup
        category_revenue = [
            ("Electronics", Decimal("5000.00")),
            ("Clothing", Decimal("3000.00")),
            ("Books", Decimal("1500.00"))
        ]
        mock_session.exec.return_value.all.return_value = category_revenue

        # Execute
        result = service.get_revenue_by_product_category()

        # Assert
        assert len(result) == 3
        assert result["Electronics"] == Decimal("5000.00")
        assert result["Books"] == Decimal("1500.00")

    def test_calculate_average_revenue_per_user(self, service, mock_session):
        """Test calculating average revenue per user (ARPU)."""
        # Setup
        total_revenue = Decimal("50000.00")
        total_users = 500
        
        mock_session.exec.return_value.scalar.side_effect = [total_revenue, total_users]

        # Execute
        result = service.calculate_average_revenue_per_user()

        # Assert
        assert result == Decimal("100.00")  # 50000 / 500
        assert mock_session.exec.call_count == 2

    def test_get_top_revenue_generating_products(self, service, mock_session):
        """Test getting top revenue generating products."""
        # Setup
        top_products = [
            ("Product A", Decimal("2500.00")),
            ("Product B", Decimal("2000.00")),
            ("Product C", Decimal("1800.00"))
        ]
        mock_session.exec.return_value.all.return_value = top_products

        # Execute
        result = service.get_top_revenue_generating_products(limit=3)

        # Assert
        assert len(result) == 3
        assert result[0][1] == Decimal("2500.00")  # Top product revenue
        assert result[2][0] == "Product C"

    def test_get_revenue_growth_rate(self, service, mock_session):
        """Test calculating revenue growth rate."""
        # Setup
        current_period_revenue = Decimal("12000.00")
        previous_period_revenue = Decimal("10000.00")
        
        mock_session.exec.return_value.scalar.side_effect = [
            current_period_revenue, previous_period_revenue
        ]

        # Execute
        result = service.get_revenue_growth_rate()

        # Assert
        assert result == Decimal("20.00")  # (12000 - 10000) / 10000 * 100
        assert mock_session.exec.call_count == 2

    def test_get_revenue_by_payment_method(self, service, mock_session):
        """Test getting revenue breakdown by payment method."""
        # Setup
        payment_revenue = [
            ("CREDIT_CARD", Decimal("8000.00")),
            ("PAYPAL", Decimal("3000.00")),
            ("BANK_TRANSFER", Decimal("1000.00"))
        ]
        mock_session.exec.return_value.all.return_value = payment_revenue

        # Execute
        result = service.get_revenue_by_payment_method()

        # Assert
        assert len(result) == 3
        assert result["CREDIT_CARD"] == Decimal("8000.00")
        assert result["PAYPAL"] == Decimal("3000.00")

    def test_calculate_revenue_per_transaction(self, service, mock_session):
        """Test calculating average revenue per transaction."""
        # Setup
        total_revenue = Decimal("25000.00")
        total_transactions = 250
        
        mock_session.exec.return_value.scalar.side_effect = [total_revenue, total_transactions]

        # Execute
        result = service.calculate_revenue_per_transaction()

        # Assert
        assert result == Decimal("100.00")  # 25000 / 250
        assert mock_session.exec.call_count == 2

    def test_get_seasonal_revenue_patterns(self, service, mock_session):
        """Test identifying seasonal revenue patterns."""
        # Setup
        seasonal_data = [
            ("Q1", Decimal("20000.00")),
            ("Q2", Decimal("22000.00")),
            ("Q3", Decimal("18000.00")),
            ("Q4", Decimal("35000.00"))  # Holiday season peak
        ]
        mock_session.exec.return_value.all.return_value = seasonal_data

        # Execute
        result = service.get_seasonal_revenue_patterns()

        # Assert
        assert len(result) == 4
        assert result["Q4"] == Decimal("35000.00")  # Holiday peak
        assert result["Q3"] == Decimal("18000.00")  # Summer low

    def test_get_refund_impact_on_revenue(self, service, mock_session):
        """Test calculating refund impact on revenue."""
        # Setup
        total_revenue = Decimal("50000.00")
        total_refunds = Decimal("2500.00")
        
        mock_session.exec.return_value.scalar.side_effect = [total_revenue, total_refunds]

        # Execute
        result = service.get_refund_impact_on_revenue()

        # Assert
        assert result["total_revenue"] == Decimal("50000.00")
        assert result["total_refunds"] == Decimal("2500.00")
        assert result["net_revenue"] == Decimal("47500.00")
        assert result["refund_rate"] == Decimal("5.00")  # 2500/50000 * 100

    def test_get_revenue_by_customer_segment(self, service, mock_session):
        """Test getting revenue by customer segments."""
        # Setup
        segment_revenue = [
            ("VIP", Decimal("15000.00")),
            ("Regular", Decimal("8000.00")),
            ("New", Decimal("3000.00"))
        ]
        mock_session.exec.return_value.all.return_value = segment_revenue

        # Execute
        result = service.get_revenue_by_customer_segment()

        # Assert
        assert len(result) == 3
        assert result["VIP"] == Decimal("15000.00")
        assert result["New"] == Decimal("3000.00")

    def test_calculate_revenue_forecast(self, service, mock_session):
        """Test calculating revenue forecast based on trends."""
        # Setup
        historical_data = [
            Decimal("8000.00"),
            Decimal("9000.00"),
            Decimal("10000.00"),
            Decimal("11000.00")
        ]
        mock_session.exec.return_value.all.return_value = [(x,) for x in historical_data]

        # Execute
        result = service.calculate_revenue_forecast(periods=2)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 2
        for forecast in result:
            assert isinstance(forecast, Decimal)
            assert forecast > Decimal("0")

    def test_get_revenue_by_geographic_region(self, service, mock_session):
        """Test getting revenue by geographic regions."""
        # Setup
        regional_revenue = [
            ("North America", Decimal("20000.00")),
            ("Europe", Decimal("15000.00")),
            ("Asia", Decimal("10000.00")),
            ("Other", Decimal("5000.00"))
        ]
        mock_session.exec.return_value.all.return_value = regional_revenue

        # Execute
        result = service.get_revenue_by_geographic_region()

        # Assert
        assert len(result) == 4
        assert result["North America"] == Decimal("20000.00")
        assert result["Asia"] == Decimal("10000.00")

    def test_calculate_customer_lifetime_value(self, service, mock_session):
        """Test calculating customer lifetime value (CLV)."""
        # Setup
        avg_order_value = Decimal("75.00")
        avg_orders_per_year = 4
        avg_customer_lifespan = 3  # years
        
        # Mock multiple queries for CLV calculation
        mock_session.exec.return_value.scalar.side_effect = [
            avg_order_value, avg_orders_per_year, avg_customer_lifespan
        ]

        # Execute
        result = service.calculate_customer_lifetime_value()

        # Assert
        expected_clv = avg_order_value * avg_orders_per_year * avg_customer_lifespan
        assert result == expected_clv  # 75 * 4 * 3 = 900

    def test_get_revenue_concentration_analysis(self, service, mock_session):
        """Test analyzing revenue concentration (80/20 rule)."""
        # Setup
        customer_revenue = [
            ("Customer A", Decimal("5000.00")),
            ("Customer B", Decimal("3000.00")),
            ("Customer C", Decimal("2000.00")),
            ("Customer D", Decimal("1000.00"))
        ]
        mock_session.exec.return_value.all.return_value = customer_revenue

        # Execute
        result = service.get_revenue_concentration_analysis()

        # Assert
        assert isinstance(result, dict)
        assert "top_20_percent_revenue" in result
        assert "total_revenue" in result
        assert "concentration_ratio" in result

    def test_get_revenue_per_acquisition_channel(self, service, mock_session):
        """Test getting revenue by customer acquisition channels."""
        # Setup
        channel_revenue = [
            ("Organic Search", Decimal("8000.00")),
            ("Social Media", Decimal("5000.00")),
            ("Email Marketing", Decimal("3000.00")),
            ("Direct", Decimal("4000.00"))
        ]
        mock_session.exec.return_value.all.return_value = channel_revenue

        # Execute
        result = service.get_revenue_per_acquisition_channel()

        # Assert
        assert len(result) == 4
        assert result["Organic Search"] == Decimal("8000.00")
        assert result["Email Marketing"] == Decimal("3000.00")

    def test_calculate_revenue_variance(self, service, mock_session):
        """Test calculating revenue variance and volatility."""
        # Setup
        monthly_revenues = [
            Decimal("8000.00"),
            Decimal("9000.00"),
            Decimal("7500.00"),
            Decimal("10500.00"),
            Decimal("9500.00")
        ]
        mock_session.exec.return_value.all.return_value = [(x,) for x in monthly_revenues]

        # Execute
        result = service.calculate_revenue_variance()

        # Assert
        assert isinstance(result, dict)
        assert "mean_revenue" in result
        assert "variance" in result
        assert "standard_deviation" in result
        assert result["mean_revenue"] > Decimal("0")

    def test_get_revenue_attribution_analysis(self, service, mock_session):
        """Test revenue attribution to marketing campaigns."""
        # Setup
        attribution_data = [
            ("Campaign A", Decimal("3000.00")),
            ("Campaign B", Decimal("2500.00")),
            ("Organic", Decimal("5000.00"))
        ]
        mock_session.exec.return_value.all.return_value = attribution_data

        # Execute
        result = service.get_revenue_attribution_analysis()

        # Assert
        assert len(result) == 3
        assert result["Organic"] == Decimal("5000.00")
        assert result["Campaign A"] == Decimal("3000.00")

    def test_export_revenue_report(self, service):
        """Test exporting revenue analytics report."""
        # Setup
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        format_type = "csv"

        # Execute
        result = service.export_revenue_report(start_date, end_date, format_type)

        # Assert
        assert isinstance(result, (str, bytes, dict))  # Could be file path, content, or metadata

    def test_get_revenue_summary_dashboard(self, service, mock_session):
        """Test getting comprehensive revenue summary for dashboard."""
        # Setup - Mock multiple database calls
        mock_session.exec.return_value.scalar.side_effect = [
            Decimal("50000.00"),  # total revenue
            Decimal("45000.00"),  # previous period revenue
            Decimal("100.00"),    # average order value
            500                   # total customers
        ]

        # Execute
        result = service.get_revenue_summary_dashboard()

        # Assert
        assert isinstance(result, dict)
        assert "total_revenue" in result
        assert "growth_rate" in result
        assert "average_order_value" in result
        assert "revenue_per_customer" in result
        assert result["total_revenue"] == Decimal("50000.00")
        assert result["growth_rate"] == Decimal("11.11")  # (50000-45000)/45000*100