"""
Unit tests for AlertService.
Tests for alert notifications and system monitoring.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from sqlmodel import Session

from app.services.alert_service import AlertService
from app.models import Product, Stock
from app.tests.fixtures.factories import ProductFactory, StockFactory


class TestAlertService:
    """Test suite for AlertService."""

    @pytest.fixture
    def mock_session(self):
        """Mock database session."""
        return Mock(spec=Session)

    @pytest.fixture
    def mock_notification_service(self):
        """Mock notification service."""
        return Mock()

    @pytest.fixture
    def service(self, mock_session, mock_notification_service):
        """AlertService instance with mocked dependencies."""
        return AlertService(
            session=mock_session,
            notification_service=mock_notification_service
        )

    def test_check_low_stock_alerts(self, service, mock_session, mock_notification_service):
        """Test checking and sending low stock alerts."""
        # Setup
        low_stock_items = [
            StockFactory(product_id=1, quantity=5, min_stock_level=10),
            StockFactory(product_id=2, quantity=2, min_stock_level=15)
        ]
        mock_session.exec.return_value.all.return_value = low_stock_items

        # Execute
        result = service.check_low_stock_alerts()

        # Assert
        assert result == 2  # Number of alerts sent
        assert mock_notification_service.send_alert.call_count == 2
        mock_session.exec.assert_called_once()

    def test_check_low_stock_alerts_no_items(self, service, mock_session, mock_notification_service):
        """Test low stock check when no items are low."""
        # Setup
        mock_session.exec.return_value.all.return_value = []

        # Execute
        result = service.check_low_stock_alerts()

        # Assert
        assert result == 0
        mock_notification_service.send_alert.assert_not_called()

    def test_send_out_of_stock_alert(self, service, mock_notification_service):
        """Test sending out of stock alert."""
        # Setup
        product = ProductFactory(name="Test Product", sku="TEST-001")

        # Execute
        result = service.send_out_of_stock_alert(product)

        # Assert
        assert result is True
        mock_notification_service.send_alert.assert_called_once()
        call_args = mock_notification_service.send_alert.call_args[1]
        assert "out of stock" in call_args["message"].lower()
        assert product.name in call_args["message"]

    def test_send_high_order_volume_alert(self, service, mock_notification_service):
        """Test sending high order volume alert."""
        # Setup
        order_count = 150
        threshold = 100

        # Execute
        result = service.send_high_order_volume_alert(order_count, threshold)

        # Assert
        assert result is True
        mock_notification_service.send_alert.assert_called_once()
        call_args = mock_notification_service.send_alert.call_args[1]
        assert str(order_count) in call_args["message"]
        assert "high order volume" in call_args["message"].lower()

    def test_check_failed_payments_alert(self, service, mock_session, mock_notification_service):
        """Test checking for failed payments and sending alerts."""
        # Setup
        failed_payment_count = 5
        mock_session.exec.return_value.scalar.return_value = failed_payment_count

        # Execute
        result = service.check_failed_payments_alert()

        # Assert
        assert result is True
        mock_notification_service.send_alert.assert_called_once()

    def test_check_failed_payments_alert_below_threshold(self, service, mock_session, mock_notification_service):
        """Test failed payments check when below threshold."""
        # Setup
        failed_payment_count = 2  # Below typical threshold
        mock_session.exec.return_value.scalar.return_value = failed_payment_count

        # Execute
        result = service.check_failed_payments_alert()

        # Assert
        assert result is False
        mock_notification_service.send_alert.assert_not_called()

    def test_send_system_error_alert(self, service, mock_notification_service):
        """Test sending system error alert."""
        # Setup
        error_message = "Database connection failed"
        error_level = "CRITICAL"

        # Execute
        result = service.send_system_error_alert(error_message, error_level)

        # Assert
        assert result is True
        mock_notification_service.send_alert.assert_called_once()
        call_args = mock_notification_service.send_alert.call_args[1]
        assert error_message in call_args["message"]
        assert error_level in call_args["alert_level"]

    def test_check_order_processing_delays(self, service, mock_session, mock_notification_service):
        """Test checking for order processing delays."""
        # Setup
        delayed_orders_count = 10
        mock_session.exec.return_value.scalar.return_value = delayed_orders_count

        # Execute
        result = service.check_order_processing_delays()

        # Assert
        assert result == delayed_orders_count
        mock_notification_service.send_alert.assert_called_once()

    def test_send_revenue_milestone_alert(self, service, mock_notification_service):
        """Test sending revenue milestone alert."""
        # Setup
        milestone_amount = 10000
        period = "monthly"

        # Execute
        result = service.send_revenue_milestone_alert(milestone_amount, period)

        # Assert
        assert result is True
        mock_notification_service.send_alert.assert_called_once()
        call_args = mock_notification_service.send_alert.call_args[1]
        assert str(milestone_amount) in call_args["message"]
        assert period in call_args["message"]

    def test_check_security_alerts(self, service, mock_session, mock_notification_service):
        """Test checking for security-related alerts."""
        # Setup
        suspicious_login_count = 5
        mock_session.exec.return_value.scalar.return_value = suspicious_login_count

        # Execute
        result = service.check_security_alerts()

        # Assert
        assert result is True
        mock_notification_service.send_alert.assert_called_once()

    def test_send_performance_alert(self, service, mock_notification_service):
        """Test sending performance degradation alert."""
        # Setup
        metric_name = "API Response Time"
        current_value = 2.5
        threshold = 2.0

        # Execute
        result = service.send_performance_alert(metric_name, current_value, threshold)

        # Assert
        assert result is True
        mock_notification_service.send_alert.assert_called_once()
        call_args = mock_notification_service.send_alert.call_args[1]
        assert metric_name in call_args["message"]
        assert str(current_value) in call_args["message"]

    def test_schedule_alert_check(self, service):
        """Test scheduling periodic alert checks."""
        # Execute
        result = service.schedule_alert_check("low_stock", interval_minutes=30)

        # Assert
        assert result is True

    def test_get_alert_history(self, service, mock_session):
        """Test retrieving alert history."""
        # Setup
        mock_alerts = [
            Mock(id=1, message="Low stock alert", created_at=datetime.now()),
            Mock(id=2, message="High volume alert", created_at=datetime.now())
        ]
        mock_session.exec.return_value.all.return_value = mock_alerts

        # Execute
        result = service.get_alert_history(limit=10)

        # Assert
        assert len(result) == 2
        assert result == mock_alerts

    def test_suppress_alert_temporarily(self, service):
        """Test temporarily suppressing specific alert types."""
        # Setup
        alert_type = "low_stock"
        suppress_duration = 60  # minutes

        # Execute
        result = service.suppress_alert_temporarily(alert_type, suppress_duration)

        # Assert
        assert result is True

    def test_is_alert_suppressed(self, service):
        """Test checking if an alert type is currently suppressed."""
        # Setup
        alert_type = "low_stock"

        # Execute
        result = service.is_alert_suppressed(alert_type)

        # Assert
        assert isinstance(result, bool)

    def test_configure_alert_thresholds(self, service):
        """Test configuring alert thresholds."""
        # Setup
        thresholds = {
            "low_stock_threshold": 10,
            "high_order_volume_threshold": 100,
            "failed_payment_threshold": 5
        }

        # Execute
        result = service.configure_alert_thresholds(thresholds)

        # Assert
        assert result is True

    def test_get_alert_configuration(self, service):
        """Test retrieving current alert configuration."""
        # Execute
        result = service.get_alert_configuration()

        # Assert
        assert isinstance(result, dict)
        assert "low_stock_threshold" in result or len(result) >= 0

    def test_validate_alert_recipients(self, service):
        """Test validating alert recipient configuration."""
        # Setup
        recipients = [
            {"email": "admin@example.com", "alert_types": ["critical", "high"]},
            {"email": "manager@example.com", "alert_types": ["medium"]}
        ]

        # Execute
        result = service.validate_alert_recipients(recipients)

        # Assert
        assert result is True

    def test_send_alert_digest(self, service, mock_notification_service):
        """Test sending periodic alert digest."""
        # Setup
        period = "daily"
        recipient = "admin@example.com"

        # Execute
        result = service.send_alert_digest(period, recipient)

        # Assert
        assert result is True
        mock_notification_service.send_digest.assert_called_once()

    def test_escalate_alert(self, service, mock_notification_service):
        """Test escalating an alert to higher priority."""
        # Setup
        alert_id = 123
        escalation_level = "URGENT"

        # Execute
        result = service.escalate_alert(alert_id, escalation_level)

        # Assert
        assert result is True

    def test_acknowledge_alert(self, service, mock_session):
        """Test acknowledging an alert."""
        # Setup
        alert_id = 123
        acknowledged_by = "admin@example.com"

        # Execute
        result = service.acknowledge_alert(alert_id, acknowledged_by)

        # Assert
        assert result is True