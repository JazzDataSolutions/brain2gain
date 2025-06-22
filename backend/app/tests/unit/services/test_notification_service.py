"""
Unit tests for NotificationService
"""
from unittest.mock import AsyncMock, patch

import pytest

from app.services.notification_service import (
    NotificationService,
    NotificationTemplate,
    NotificationType,
)


class TestNotificationService:
    """Test cases for NotificationService"""

    @pytest.fixture
    def mock_session(self):
        """Mock database session"""
        session = AsyncMock()
        return session

    @pytest.fixture
    def notification_service(self, mock_session):
        """Create NotificationService instance with mocked session"""
        return NotificationService(mock_session)

    @pytest.mark.asyncio
    async def test_notify_order_status_success(self, notification_service):
        """Test successful order status notification"""
        with patch('app.services.notification_service.manager') as mock_manager:
            mock_manager.send_personal_message = AsyncMock()
            mock_manager.broadcast_to_role = AsyncMock()

            result = await notification_service.notify_order_status(
                order_id="12345",
                status="shipped",
                customer_id="user123"
            )

            assert result["success"] is True
            assert "Order status notification sent" in result["message"]

            # Verify WebSocket calls
            mock_manager.send_personal_message.assert_called_once()
            mock_manager.broadcast_to_role.assert_called_once()

    @pytest.mark.asyncio
    async def test_notify_low_stock_success(self, notification_service):
        """Test successful low stock notification"""
        with patch('app.services.notification_service.manager') as mock_manager:
            mock_manager.broadcast_to_role = AsyncMock()

            result = await notification_service.notify_low_stock(
                product_id="prod123",
                product_name="Whey Protein",
                stock_quantity=5,
                min_stock=10
            )

            assert result["success"] is True
            assert "Low stock notification sent" in result["message"]

            # Verify WebSocket calls
            assert mock_manager.broadcast_to_role.call_count == 2  # admin and manager

    @pytest.mark.asyncio
    async def test_notify_new_order_success(self, notification_service):
        """Test successful new order notification"""
        with patch('app.services.notification_service.manager') as mock_manager:
            mock_manager.broadcast_to_role = AsyncMock()

            result = await notification_service.notify_new_order(
                order_id="order123",
                customer_name="John Doe",
                total_amount=156.99
            )

            assert result["success"] is True
            assert "New order notification sent" in result["message"]

            # Verify WebSocket calls
            assert mock_manager.broadcast_to_role.call_count == 2  # admin and seller

    @pytest.mark.asyncio
    async def test_send_system_alert_success(self, notification_service):
        """Test successful system alert"""
        with patch('app.services.notification_service.manager') as mock_manager:
            mock_manager.broadcast_to_role = AsyncMock()

            result = await notification_service.send_system_alert(
                message="System maintenance in 10 minutes",
                alert_type="warning",
                target_roles=["admin", "manager"]
            )

            assert result["success"] is True
            assert "System alert sent" in result["message"]

            # Verify WebSocket calls
            assert mock_manager.broadcast_to_role.call_count == 2  # admin and manager

    @pytest.mark.asyncio
    async def test_websocket_error_handling(self, notification_service):
        """Test error handling when WebSocket fails"""
        with patch('app.services.notification_service.manager') as mock_manager:
            mock_manager.send_personal_message = AsyncMock(side_effect=Exception("WebSocket error"))

            result = await notification_service.notify_order_status(
                order_id="12345",
                status="shipped",
                customer_id="user123"
            )

            assert result["success"] is False
            assert "WebSocket error" in result["error"]

    @pytest.mark.asyncio
    async def test_send_notification_email(self, notification_service):
        """Test sending email notification"""
        result = await notification_service.send_notification(
            recipient="test@example.com",
            notification_type=NotificationType.EMAIL,
            template=NotificationTemplate.ORDER_CONFIRMATION,
            data={"order_id": "12345", "customer_name": "John Doe"}
        )

        assert result["success"] is True
        assert "notification_id" in result
        assert result["status"] == "SENT"

    @pytest.mark.asyncio
    async def test_send_notification_sms(self, notification_service):
        """Test sending SMS notification"""
        result = await notification_service.send_notification(
            recipient="+1234567890",
            notification_type=NotificationType.SMS,
            template=NotificationTemplate.ORDER_SHIPPED,
            data={"order_id": "12345", "tracking_number": "TRACK123"}
        )

        assert result["success"] is True
        assert "notification_id" in result
        assert result["status"] == "SENT"

    @pytest.mark.asyncio
    async def test_bulk_notifications(self, notification_service):
        """Test bulk notification sending"""
        recipients = ["user1@example.com", "user2@example.com", "user3@example.com"]

        result = await notification_service.send_bulk_notifications(
            recipients=recipients,
            notification_type=NotificationType.EMAIL,
            template=NotificationTemplate.NEWSLETTER,
            data={"subject": "Newsletter", "content": "Monthly updates"}
        )

        assert result["total_recipients"] == 3
        assert result["successful_sends"] == 3
        assert result["failed_sends"] == 0

    @pytest.mark.asyncio
    async def test_get_notification_status(self, notification_service):
        """Test getting notification status"""
        notification_id = "notif123"

        result = await notification_service.get_notification_status(notification_id)

        assert result["notification_id"] == notification_id
        assert "status" in result
        assert "sent_at" in result

    def test_get_template_content(self, notification_service):
        """Test template content generation"""
        content = notification_service._get_template_content(
            template=NotificationTemplate.ORDER_CONFIRMATION,
            notification_type=NotificationType.EMAIL,
            data={"order_id": "12345"}
        )

        assert "subject" in content
        assert "body" in content
        assert "12345" in content["subject"]

    def test_get_order_template_mapping(self, notification_service):
        """Test order status to template mapping"""
        assert notification_service._get_order_template("confirmed") == NotificationTemplate.ORDER_CONFIRMATION
        assert notification_service._get_order_template("shipped") == NotificationTemplate.ORDER_SHIPPED
        assert notification_service._get_order_template("delivered") == NotificationTemplate.ORDER_DELIVERED
        assert notification_service._get_order_template("cancelled") == NotificationTemplate.ORDER_CANCELLED

        # Test default fallback
        assert notification_service._get_order_template("unknown") == NotificationTemplate.ORDER_CONFIRMATION
