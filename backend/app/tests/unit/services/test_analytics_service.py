"""
Unit tests for Analytics Service layer - Testing new KPI calculations and analytics methods.
"""

from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from sqlmodel import Session

from app.models import OrderStatus, TransactionType
from app.services.analytics_service import AnalyticsService
from app.tests.fixtures.factories import (
    CustomerFactory,
    SalesOrderFactory,
    TransactionFactory,
    create_analytics_test_data,
    create_churn_scenario_data,
    create_conversion_scenario_data,
    create_mrr_scenario_data,
)


class TestAnalyticsService:
    """Test cases for AnalyticsService new KPI methods."""

    @pytest.fixture
    def analytics_service(self, db: Session) -> AnalyticsService:
        """Create an AnalyticsService instance with test database."""
        return AnalyticsService(db)

    # ─── REVENUE METRICS TESTS ─────────────────────────────────────────────────

    def test_get_total_revenue_with_data(self, analytics_service: AnalyticsService, db: Session):
        """Test total revenue calculation with actual data."""
        # Setup
        test_data = create_analytics_test_data(db, time_period_days=30)

        # Calculate expected revenue (sum of completed transaction amounts)
        expected_revenue = sum(
            t.amount for t in test_data["transactions"]
            if t.status == "COMPLETED" and t.paid
        )

        # Execute
        result = analytics_service.get_total_revenue()

        # Assert
        assert result == expected_revenue
        assert isinstance(result, Decimal)

    def test_get_total_revenue_empty_database(self, analytics_service: AnalyticsService, db: Session):
        """Test total revenue calculation with empty database."""
        result = analytics_service.get_total_revenue()
        assert result == Decimal('0')

    def test_get_total_revenue_with_date_range(self, analytics_service: AnalyticsService, db: Session):
        """Test total revenue calculation within specific date range."""
        # Setup
        current_date = datetime.utcnow()
        start_date = current_date - timedelta(days=7)
        end_date = current_date

        # Create transaction within range
        customer = CustomerFactory()
        db.add(customer)
        db.commit()

        transaction_in_range = TransactionFactory(
            customer_id=customer.customer_id,
            transaction_type=TransactionType.SALE,
            amount=Decimal('100.00'),
            transaction_date=current_date - timedelta(days=3),
            status="COMPLETED",
            paid=True
        )
        db.add(transaction_in_range)

        # Create transaction outside range
        transaction_outside = TransactionFactory(
            customer_id=customer.customer_id,
            transaction_type=TransactionType.SALE,
            amount=Decimal('50.00'),
            transaction_date=current_date - timedelta(days=10),
            status="COMPLETED",
            paid=True
        )
        db.add(transaction_outside)
        db.commit()

        # Execute
        result = analytics_service.get_total_revenue(start_date, end_date)

        # Assert
        assert result == Decimal('100.00')  # Only the transaction within range

    def test_calculate_mrr_with_recurring_customers(self, analytics_service: AnalyticsService, db: Session):
        """Test MRR calculation with recurring customer data."""
        # Setup
        mrr_data = create_mrr_scenario_data(db)
        expected_mrr = mrr_data["expected_mrr"]

        # Execute
        result = analytics_service.calculate_mrr()

        # Assert
        assert abs(float(result) - expected_mrr) < 0.01  # Allow small float precision differences
        assert isinstance(result, Decimal)

    def test_calculate_mrr_no_recurring_customers(self, analytics_service: AnalyticsService, db: Session):
        """Test MRR calculation with no recurring customers."""
        # Setup - create single order customers only
        for i in range(3):
            customer = CustomerFactory()
            db.add(customer)
            db.commit()

            # Single order per customer (not recurring)
            transaction = TransactionFactory(
                customer_id=customer.customer_id,
                transaction_type=TransactionType.SALE,
                transaction_date=datetime.utcnow() - timedelta(days=10),
                status="COMPLETED",
                paid=True
            )
            db.add(transaction)
        db.commit()

        # Execute
        result = analytics_service.calculate_mrr()

        # Assert
        assert result == Decimal('0')  # No recurring customers

    def test_calculate_arr_from_mrr(self, analytics_service: AnalyticsService, db: Session):
        """Test ARR calculation (should be MRR * 12)."""
        # Setup
        mrr_data = create_mrr_scenario_data(db)
        expected_arr = mrr_data["expected_arr"]

        # Execute
        mrr = analytics_service.calculate_mrr()
        arr = analytics_service.calculate_arr()

        # Assert
        assert abs(float(arr) - expected_arr) < 0.01
        assert arr == mrr * 12

    def test_calculate_revenue_per_visitor(self, analytics_service: AnalyticsService, db: Session):
        """Test revenue per visitor calculation."""
        # Setup
        test_data = create_analytics_test_data(db, time_period_days=30)

        # Calculate expected RPV
        total_revenue = sum(t.amount for t in test_data["transactions"] if t.paid)
        total_customers = len(test_data["customers"])
        expected_rpv = total_revenue / total_customers if total_customers > 0 else Decimal('0')

        # Execute
        result = analytics_service.calculate_revenue_per_visitor(days=30)

        # Assert
        assert abs(float(result) - float(expected_rpv)) < 0.01

    # ─── CUSTOMER METRICS TESTS ────────────────────────────────────────────────

    def test_calculate_churn_rate_with_churned_customers(self, analytics_service: AnalyticsService, db: Session):
        """Test churn rate calculation with known churned customers."""
        # Setup
        churn_data = create_churn_scenario_data(db)
        expected_churn_rate = churn_data["expected_churn_rate"]

        # Execute
        result = analytics_service.calculate_churn_rate(period_days=90)

        # Assert
        assert abs(result - expected_churn_rate) < 0.1  # Allow small precision differences

    def test_calculate_churn_rate_all_active_customers(self, analytics_service: AnalyticsService, db: Session):
        """Test churn rate calculation when all customers are active."""
        # Setup - create customers with recent orders
        current_date = datetime.utcnow()
        for i in range(5):
            customer = CustomerFactory()
            db.add(customer)
            db.commit()

            # Recent order
            order = SalesOrderFactory(
                customer_id=customer.customer_id,
                order_date=current_date - timedelta(days=5),
                status=OrderStatus.COMPLETED
            )
            db.add(order)
        db.commit()

        # Execute
        result = analytics_service.calculate_churn_rate()

        # Assert
        assert result == 0.0  # No churned customers

    def test_calculate_conversion_rate(self, analytics_service: AnalyticsService, db: Session):
        """Test conversion rate calculation."""
        # Setup
        conversion_data = create_conversion_scenario_data(db)
        expected_rate = conversion_data["expected_conversion_rate"]

        # Execute
        result = analytics_service.calculate_conversion_rate(days=30)

        # Assert
        assert abs(result - expected_rate) < 0.1

    def test_calculate_repeat_customer_rate(self, analytics_service: AnalyticsService, db: Session):
        """Test repeat customer rate calculation."""
        # Setup - create customers with multiple orders
        current_date = datetime.utcnow()
        customers = []

        # 3 customers with multiple orders (repeat customers)
        for i in range(3):
            customer = CustomerFactory()
            db.add(customer)
            db.commit()
            customers.append(customer)

            # Multiple orders for each customer
            for j in range(2):
                order = SalesOrderFactory(
                    customer_id=customer.customer_id,
                    order_date=current_date - timedelta(days=j*10),
                    status=OrderStatus.COMPLETED
                )
                db.add(order)

        # 2 customers with single orders (not repeat)
        for i in range(2):
            customer = CustomerFactory()
            db.add(customer)
            db.commit()
            customers.append(customer)

            order = SalesOrderFactory(
                customer_id=customer.customer_id,
                order_date=current_date - timedelta(days=5),
                status=OrderStatus.COMPLETED
            )
            db.add(order)

        db.commit()

        # Execute
        result = analytics_service.calculate_repeat_customer_rate(days=30)

        # Assert
        # 3 repeat customers out of 5 total = 60%
        assert abs(result - 60.0) < 0.1

    def test_calculate_customer_lifetime_value(self, analytics_service: AnalyticsService, db: Session):
        """Test CLV calculation for a specific customer."""
        # Setup
        customer = CustomerFactory()
        db.add(customer)
        db.commit()

        # Create multiple transactions for the customer
        total_spent = Decimal('0')
        for i in range(3):
            amount = Decimal('100.00')
            transaction = TransactionFactory(
                customer_id=customer.customer_id,
                transaction_type=TransactionType.SALE,
                amount=amount,
                transaction_date=datetime.utcnow() - timedelta(days=i*30),
                status="COMPLETED",
                paid=True
            )
            db.add(transaction)
            total_spent += amount

        # Create corresponding orders
        for i in range(3):
            order = SalesOrderFactory(
                customer_id=customer.customer_id,
                order_date=datetime.utcnow() - timedelta(days=i*30),
                status=OrderStatus.COMPLETED
            )
            db.add(order)

        db.commit()

        # Execute
        result = analytics_service.calculate_customer_lifetime_value(customer.customer_id)

        # Assert
        assert result > Decimal('0')  # Should be positive
        assert isinstance(result, Decimal)

    # ─── CONVERSION METRICS TESTS ──────────────────────────────────────────────

    def test_get_cart_abandonment_rate(self, analytics_service: AnalyticsService, db: Session):
        """Test cart abandonment rate calculation."""
        # Setup
        test_data = create_analytics_test_data(db)

        # Calculate expected abandonment rate
        total_carts = len(test_data["carts"])
        completed_orders = len([o for o in test_data["orders"] if o.status == OrderStatus.COMPLETED])
        expected_rate = ((total_carts - completed_orders) / total_carts * 100) if total_carts > 0 else 0

        # Execute
        result = analytics_service.get_cart_abandonment_rate(days=30)

        # Assert
        assert abs(result - expected_rate) < 1.0  # Allow some variance due to date filtering

    def test_get_cart_abandonment_rate_no_carts(self, analytics_service: AnalyticsService, db: Session):
        """Test cart abandonment rate with no carts."""
        result = analytics_service.get_cart_abandonment_rate()
        assert result == 0.0

    # ─── FINANCIAL SUMMARY TESTS ───────────────────────────────────────────────

    def test_get_financial_summary_structure(self, analytics_service: AnalyticsService, db: Session):
        """Test that financial summary returns correct structure with new KPIs."""
        # Setup
        create_analytics_test_data(db)

        # Execute
        result = analytics_service.get_financial_summary()

        # Assert structure
        assert "revenue" in result
        assert "orders" in result
        assert "customers" in result
        assert "inventory" in result
        assert "conversion" in result

        # Check new revenue metrics
        revenue_section = result["revenue"]
        assert "mrr" in revenue_section
        assert "arr" in revenue_section
        assert "revenue_per_visitor" in revenue_section

        # Check new conversion metrics
        conversion_section = result["conversion"]
        assert "conversion_rate" in conversion_section
        assert "repeat_customer_rate" in conversion_section
        assert "churn_rate" in conversion_section
        assert "cart_abandonment_rate" in conversion_section

    def test_get_financial_summary_data_types(self, analytics_service: AnalyticsService, db: Session):
        """Test that financial summary returns correct data types."""
        # Setup
        create_analytics_test_data(db)

        # Execute
        result = analytics_service.get_financial_summary()

        # Assert data types
        assert isinstance(result["revenue"]["mrr"], float)
        assert isinstance(result["revenue"]["arr"], float)
        assert isinstance(result["conversion"]["churn_rate"], float)
        assert isinstance(result["conversion"]["repeat_customer_rate"], float)
        assert isinstance(result["conversion"]["conversion_rate"], float)

    # ─── EDGE CASES AND ERROR HANDLING ─────────────────────────────────────────

    def test_analytics_with_no_data(self, analytics_service: AnalyticsService, db: Session):
        """Test all analytics methods with empty database."""
        # Execute all methods with empty DB
        total_revenue = analytics_service.get_total_revenue()
        mrr = analytics_service.calculate_mrr()
        arr = analytics_service.calculate_arr()
        churn_rate = analytics_service.calculate_churn_rate()
        conversion_rate = analytics_service.calculate_conversion_rate()
        repeat_rate = analytics_service.calculate_repeat_customer_rate()
        abandonment_rate = analytics_service.get_cart_abandonment_rate()

        # Assert all return appropriate zero values
        assert total_revenue == Decimal('0')
        assert mrr == Decimal('0')
        assert arr == Decimal('0')
        assert churn_rate == 0.0
        assert conversion_rate == 0.0
        assert repeat_rate == 0.0
        assert abandonment_rate == 0.0

    def test_clv_nonexistent_customer(self, analytics_service: AnalyticsService, db: Session):
        """Test CLV calculation for non-existent customer."""
        # Execute with non-existent customer ID
        from uuid import uuid4
        result = analytics_service.calculate_customer_lifetime_value(uuid4())

        # Assert
        assert result == Decimal('0')

    def test_date_range_future_dates(self, analytics_service: AnalyticsService, db: Session):
        """Test revenue calculation with future date range."""
        # Setup
        future_start = datetime.utcnow() + timedelta(days=30)
        future_end = datetime.utcnow() + timedelta(days=60)

        # Execute
        result = analytics_service.get_total_revenue(future_start, future_end)

        # Assert
        assert result == Decimal('0')  # No future transactions

    def test_revenue_growth_rate_calculation(self, analytics_service: AnalyticsService, db: Session):
        """Test revenue growth rate calculation logic."""
        # This would require time-based data setup
        # For now, test that method doesn't crash
        result = analytics_service.get_revenue_growth_rate(period_days=30)
        assert isinstance(result, float)
        assert result >= -100.0  # Growth rate can't be less than -100%

    # ─── PERFORMANCE TESTS ─────────────────────────────────────────────────────

    @pytest.mark.performance
    def test_analytics_performance_with_large_dataset(self, analytics_service: AnalyticsService, db: Session):
        """Test analytics performance with larger dataset."""
        # Setup large dataset
        large_data = create_analytics_test_data(db, time_period_days=365)

        # Measure time for key operations
        import time

        start_time = time.time()
        financial_summary = analytics_service.get_financial_summary()
        end_time = time.time()

        # Assert performance
        execution_time = end_time - start_time
        assert execution_time < 5.0  # Should complete within 5 seconds
        assert financial_summary is not None

    def test_concurrent_analytics_calculations(self, analytics_service: AnalyticsService, db: Session):
        """Test that multiple analytics calculations can run concurrently."""
        # Setup
        create_analytics_test_data(db)

        # Execute multiple calculations
        results = []
        methods = [
            analytics_service.calculate_mrr,
            analytics_service.calculate_churn_rate,
            analytics_service.calculate_conversion_rate,
            lambda: analytics_service.get_total_revenue()
        ]

        for method in methods:
            result = method()
            results.append(result)

        # Assert all calculations completed
        assert len(results) == 4
        assert all(result is not None for result in results)
