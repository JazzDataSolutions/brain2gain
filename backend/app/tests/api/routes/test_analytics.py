"""
Integration tests for Analytics API endpoints.
"""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.tests.fixtures.factories import (
    create_analytics_test_data,
    create_churn_scenario_data,
    create_conversion_scenario_data,
    create_mrr_scenario_data,
)


class TestAnalyticsAPI:
    """Test cases for Analytics API endpoints."""

    def test_get_financial_summary_success(
        self, client: TestClient, superuser_token_headers: dict[str, str], db: Session
    ):
        """Test successful financial summary retrieval."""
        # Setup
        create_analytics_test_data(db)

        # Execute
        response = client.get(
            "/api/analytics/financial-summary", headers=superuser_token_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Check structure
        assert "revenue" in data
        assert "orders" in data
        assert "customers" in data
        assert "inventory" in data
        assert "conversion" in data

        # Check new KPI fields
        revenue = data["revenue"]
        assert "mrr" in revenue
        assert "arr" in revenue
        assert "revenue_per_visitor" in revenue

        conversion = data["conversion"]
        assert "conversion_rate" in conversion
        assert "repeat_customer_rate" in conversion
        assert "churn_rate" in conversion

    def test_get_financial_summary_unauthorized(self, client: TestClient):
        """Test financial summary access without authentication."""
        response = client.get("/api/analytics/financial-summary")
        assert response.status_code == 401

    def test_get_financial_summary_non_admin(
        self, client: TestClient, normal_user_token_headers: dict[str, str]
    ):
        """Test financial summary access with non-admin user."""
        response = client.get(
            "/api/analytics/financial-summary", headers=normal_user_token_headers
        )
        assert response.status_code == 403

    @patch("app.core.cache.CacheService.get")
    @patch("app.core.cache.CacheService.set")
    def test_get_financial_summary_with_cache(
        self,
        mock_cache_set,
        mock_cache_get,
        client: TestClient,
        superuser_token_headers: dict[str, str],
        db: Session,
    ):
        """Test financial summary with cache hit."""
        # Setup cache mock
        cached_data = {
            "revenue": {"today": 1000, "mrr": 5000, "arr": 60000},
            "orders": {"orders_today": 10},
            "customers": {"total_customers": 100},
            "inventory": {"total_products": 50},
            "conversion": {"churn_rate": 5.0},
        }
        mock_cache_get.return_value = cached_data

        # Execute
        response = client.get(
            "/api/analytics/financial-summary", headers=superuser_token_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data == cached_data
        mock_cache_get.assert_called_once_with("analytics:financial_summary")
        mock_cache_set.assert_not_called()  # Should not set cache on hit

    def test_get_realtime_metrics_success(
        self, client: TestClient, superuser_token_headers: dict[str, str], db: Session
    ):
        """Test successful realtime metrics retrieval."""
        # Setup
        create_analytics_test_data(db)

        # Execute
        response = client.get(
            "/api/analytics/realtime-metrics", headers=superuser_token_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Check required fields
        assert "current_revenue_today" in data
        assert "orders_today" in data
        assert "pending_orders" in data
        assert "active_carts" in data
        assert "low_stock_alerts" in data
        assert "timestamp" in data

    def test_get_mrr_endpoint(
        self, client: TestClient, superuser_token_headers: dict[str, str], db: Session
    ):
        """Test MRR endpoint."""
        # Setup
        mrr_data = create_mrr_scenario_data(db)

        # Execute
        response = client.get(
            "/api/analytics/revenue/mrr", headers=superuser_token_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "mrr" in data
        assert "currency" in data
        assert "calculation_date" in data
        assert data["currency"] == "USD"
        assert abs(data["mrr"] - mrr_data["expected_mrr"]) < 0.01

    def test_get_arr_endpoint(
        self, client: TestClient, superuser_token_headers: dict[str, str], db: Session
    ):
        """Test ARR endpoint."""
        # Setup
        mrr_data = create_mrr_scenario_data(db)

        # Execute
        response = client.get(
            "/api/analytics/revenue/arr", headers=superuser_token_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "arr" in data
        assert "currency" in data
        assert "calculation_date" in data
        assert abs(data["arr"] - mrr_data["expected_arr"]) < 0.01

    def test_get_conversion_rate_endpoint(
        self, client: TestClient, superuser_token_headers: dict[str, str], db: Session
    ):
        """Test conversion rate endpoint."""
        # Setup
        conversion_data = create_conversion_scenario_data(db)

        # Execute
        response = client.get(
            "/api/analytics/conversion/rate?days=30", headers=superuser_token_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "conversion_rate_percentage" in data
        assert "analysis_period_days" in data
        assert "calculation_date" in data
        assert data["analysis_period_days"] == 30
        assert (
            abs(
                data["conversion_rate_percentage"]
                - conversion_data["expected_conversion_rate"]
            )
            < 1.0
        )

    def test_get_churn_rate_endpoint(
        self, client: TestClient, superuser_token_headers: dict[str, str], db: Session
    ):
        """Test churn rate endpoint."""
        # Setup
        churn_data = create_churn_scenario_data(db)

        # Execute
        response = client.get(
            "/api/analytics/customers/churn-rate?period_days=90",
            headers=superuser_token_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "churn_rate_percentage" in data
        assert "retention_rate_percentage" in data
        assert "analysis_period_days" in data
        assert data["analysis_period_days"] == 90
        assert (
            abs(data["churn_rate_percentage"] - churn_data["expected_churn_rate"]) < 1.0
        )
        assert (
            abs(
                data["retention_rate_percentage"]
                - (100 - churn_data["expected_churn_rate"])
            )
            < 1.0
        )

    def test_get_repeat_customer_rate_endpoint(
        self, client: TestClient, superuser_token_headers: dict[str, str], db: Session
    ):
        """Test repeat customer rate endpoint."""
        # Setup
        create_analytics_test_data(db)

        # Execute
        response = client.get(
            "/api/analytics/customers/repeat-rate?days=30",
            headers=superuser_token_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "repeat_customer_rate_percentage" in data
        assert "analysis_period_days" in data
        assert "calculation_date" in data
        assert data["analysis_period_days"] == 30

    def test_get_revenue_per_visitor_endpoint(
        self, client: TestClient, superuser_token_headers: dict[str, str], db: Session
    ):
        """Test revenue per visitor endpoint."""
        # Setup
        create_analytics_test_data(db)

        # Execute
        response = client.get(
            "/api/analytics/revenue/per-visitor?days=30",
            headers=superuser_token_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "revenue_per_visitor" in data
        assert "currency" in data
        assert "analysis_period_days" in data
        assert "calculation_date" in data
        assert data["currency"] == "USD"
        assert data["analysis_period_days"] == 30

    def test_get_alert_summary_endpoint(
        self, client: TestClient, superuser_token_headers: dict[str, str], db: Session
    ):
        """Test alert summary endpoint."""
        # Execute
        response = client.get(
            "/api/analytics/alerts/summary", headers=superuser_token_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "total_alerts" in data
        assert "critical_alerts" in data
        assert "warning_alerts" in data
        assert "info_alerts" in data
        assert "last_checked" in data
        assert "alerts" in data
        assert isinstance(data["alerts"], list)

    def test_get_date_range_metrics_endpoint(
        self, client: TestClient, superuser_token_headers: dict[str, str], db: Session
    ):
        """Test date range metrics endpoint."""
        # Setup
        create_analytics_test_data(db, time_period_days=30)

        start_date = (datetime.utcnow() - timedelta(days=7)).isoformat()
        end_date = datetime.utcnow().isoformat()

        # Execute
        response = client.get(
            f"/api/analytics/metrics/date-range?start_date={start_date}&end_date={end_date}",
            headers=superuser_token_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "date_range" in data
        assert "revenue" in data
        assert "orders" in data
        assert "conversion" in data
        assert "calculated_at" in data

        date_range = data["date_range"]
        assert "start_date" in date_range
        assert "end_date" in date_range
        assert "days" in date_range
        assert date_range["days"] == 8  # 7 days + 1 (inclusive)

    def test_get_revenue_trends_endpoint(
        self, client: TestClient, superuser_token_headers: dict[str, str], db: Session
    ):
        """Test revenue trends endpoint."""
        # Setup
        create_analytics_test_data(db, time_period_days=30)

        # Execute
        response = client.get(
            "/api/analytics/trends/revenue?days=7", headers=superuser_token_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "period" in data
        assert "trends" in data
        assert "statistics" in data
        assert "calculated_at" in data

        period = data["period"]
        assert period["days"] == 7

        trends = data["trends"]
        assert len(trends) == 7
        assert all("date" in trend for trend in trends)
        assert all("revenue" in trend for trend in trends)
        assert all("day_of_week" in trend for trend in trends)

        statistics = data["statistics"]
        assert "average_daily_revenue" in statistics
        assert "highest_day_revenue" in statistics
        assert "lowest_day_revenue" in statistics
        assert "growth_rate_percentage" in statistics
        assert "total_revenue" in statistics

    def test_invalidate_cache_endpoint(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ):
        """Test cache invalidation endpoint."""
        # Execute
        response = client.delete(
            "/api/analytics/cache/invalidate?pattern=analytics:*",
            headers=superuser_token_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "message" in data
        assert "pattern" in data
        assert "deleted_keys" in data
        assert "timestamp" in data
        assert data["pattern"] == "analytics:*"

    def test_get_cache_stats_endpoint(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ):
        """Test cache statistics endpoint."""
        # Execute
        response = client.get(
            "/api/analytics/cache/stats", headers=superuser_token_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "cache_stats" in data
        assert "timestamp" in data

        cache_stats = data["cache_stats"]
        assert "type" in cache_stats
        assert "connected" in cache_stats

    # ─── ERROR HANDLING TESTS ──────────────────────────────────────────────────

    def test_conversion_rate_invalid_days_parameter(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ):
        """Test conversion rate endpoint with invalid days parameter."""
        # Execute with invalid days parameter
        response = client.get(
            "/api/analytics/conversion/rate?days=0", headers=superuser_token_headers
        )

        # Assert
        assert response.status_code == 422  # Validation error

    def test_churn_rate_invalid_period(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ):
        """Test churn rate endpoint with invalid period parameter."""
        # Execute with invalid period
        response = client.get(
            "/api/analytics/customers/churn-rate?period_days=29",  # Below minimum
            headers=superuser_token_headers,
        )

        # Assert
        assert response.status_code == 422  # Validation error

    def test_date_range_metrics_missing_parameters(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ):
        """Test date range metrics endpoint with missing required parameters."""
        # Execute without required parameters
        response = client.get(
            "/api/analytics/metrics/date-range", headers=superuser_token_headers
        )

        # Assert
        assert response.status_code == 422  # Validation error

    def test_date_range_metrics_invalid_date_format(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ):
        """Test date range metrics endpoint with invalid date format."""
        # Execute with invalid date format
        response = client.get(
            "/api/analytics/metrics/date-range?start_date=invalid&end_date=also-invalid",
            headers=superuser_token_headers,
        )

        # Assert
        assert response.status_code == 422  # Validation error

    def test_revenue_trends_out_of_range_days(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ):
        """Test revenue trends endpoint with out-of-range days parameter."""
        # Execute with days parameter above maximum
        response = client.get(
            "/api/analytics/trends/revenue?days=400",  # Above maximum of 365
            headers=superuser_token_headers,
        )

        # Assert
        assert response.status_code == 422  # Validation error

    # ─── PERFORMANCE TESTS ─────────────────────────────────────────────────────

    @pytest.mark.performance
    def test_financial_summary_response_time(
        self, client: TestClient, superuser_token_headers: dict[str, str], db: Session
    ):
        """Test financial summary endpoint response time."""
        # Setup larger dataset
        create_analytics_test_data(db, time_period_days=365)

        import time

        # Execute with timing
        start_time = time.time()
        response = client.get(
            "/api/analytics/financial-summary", headers=superuser_token_headers
        )
        end_time = time.time()

        # Assert
        assert response.status_code == 200
        response_time = end_time - start_time
        assert response_time < 3.0  # Should respond within 3 seconds

    @pytest.mark.performance
    def test_multiple_concurrent_requests(
        self, client: TestClient, superuser_token_headers: dict[str, str], db: Session
    ):
        """Test multiple concurrent analytics requests."""
        # Setup
        create_analytics_test_data(db)

        import concurrent.futures
        import time

        def make_request(endpoint):
            start_time = time.time()
            response = client.get(endpoint, headers=superuser_token_headers)
            end_time = time.time()
            return response.status_code, end_time - start_time

        endpoints = [
            "/api/analytics/financial-summary",
            "/api/analytics/realtime-metrics",
            "/api/analytics/revenue/mrr",
            "/api/analytics/customers/churn-rate",
            "/api/analytics/conversion/rate",
        ]

        # Execute concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(make_request, endpoint) for endpoint in endpoints
            ]
            results = [
                future.result() for future in concurrent.futures.as_completed(futures)
            ]

        # Assert all requests succeeded
        for status_code, response_time in results:
            assert status_code == 200
            assert response_time < 5.0  # Each request should complete within 5 seconds
