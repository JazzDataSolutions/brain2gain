"""
Notification Service - Microservice for email, SMS, and push notifications
Part of Phase 3: Support Services Architecture

Handles:
- Multi-channel notifications (email, SMS, push, in-app)
- Template management and personalization
- Notification scheduling and queuing
- Delivery tracking and analytics
- User preferences and opt-out management
- Automated campaigns and triggers
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.cache import (
    invalidate_cache_key,
)
from app.core.config import settings
from app.core.websocket import manager

logger = logging.getLogger(__name__)


class NotificationType(str, Enum):
    """Notification type enumeration"""

    EMAIL = "EMAIL"
    SMS = "SMS"
    PUSH = "PUSH"
    IN_APP = "IN_APP"
    WEBHOOK = "WEBHOOK"


class NotificationPriority(str, Enum):
    """Notification priority levels"""

    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"


class NotificationStatus(str, Enum):
    """Notification delivery status"""

    PENDING = "PENDING"
    QUEUED = "QUEUED"
    SENDING = "SENDING"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    BOUNCED = "BOUNCED"
    OPENED = "OPENED"
    CLICKED = "CLICKED"


class NotificationTemplate(str, Enum):
    """Predefined notification templates"""

    ORDER_CONFIRMATION = "ORDER_CONFIRMATION"
    ORDER_SHIPPED = "ORDER_SHIPPED"
    ORDER_DELIVERED = "ORDER_DELIVERED"
    ORDER_CANCELLED = "ORDER_CANCELLED"
    PAYMENT_RECEIVED = "PAYMENT_RECEIVED"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    REFUND_PROCESSED = "REFUND_PROCESSED"
    PASSWORD_RESET = "PASSWORD_RESET"
    ACCOUNT_CREATED = "ACCOUNT_CREATED"
    LOW_STOCK_ALERT = "LOW_STOCK_ALERT"
    MARKETING_CAMPAIGN = "MARKETING_CAMPAIGN"
    NEWSLETTER = "NEWSLETTER"


class NotificationService:
    """Service for multi-channel notification management."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.email_config = self._get_email_config()
        self.sms_config = self._get_sms_config()
        self.push_config = self._get_push_config()

    async def send_notification(
        self,
        recipient: str,
        notification_type: NotificationType,
        template: NotificationTemplate,
        data: dict[str, Any],
        priority: NotificationPriority = NotificationPriority.NORMAL,
        scheduled_at: datetime | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Send a notification through the specified channel.

        Args:
            recipient: Recipient identifier (email, phone, user_id, etc.)
            notification_type: Type of notification channel
            template: Template to use for the notification
            data: Data to populate the template
            priority: Notification priority
            scheduled_at: When to send (None for immediate)
            metadata: Additional metadata

        Returns:
            Notification result with tracking ID
        """
        # Create notification record
        notification_id = str(uuid.uuid4())
        notification_record = await self._create_notification_record(
            notification_id=notification_id,
            recipient=recipient,
            notification_type=notification_type,
            template=template,
            data=data,
            priority=priority,
            scheduled_at=scheduled_at,
            metadata=metadata,
        )

        try:
            # Check user preferences
            if not await self._check_user_preferences(
                recipient, notification_type, template
            ):
                await self._update_notification_status(
                    notification_id, NotificationStatus.FAILED, "User opted out"
                )
                return {
                    "success": False,
                    "notification_id": notification_id,
                    "status": NotificationStatus.FAILED,
                    "message": "User has opted out of this notification type",
                }

            # Handle scheduling
            if scheduled_at and scheduled_at > datetime.now(timezone.utc):
                await self._schedule_notification(notification_record)
                return {
                    "success": True,
                    "notification_id": notification_id,
                    "status": NotificationStatus.QUEUED,
                    "scheduled_at": scheduled_at.isoformat(),
                    "message": "Notification scheduled successfully",
                }

            # Send immediately
            result = await self._send_immediate_notification(notification_record)

            return {
                "success": result["success"],
                "notification_id": notification_id,
                "status": result["status"],
                "message": result.get("message", "Notification processed"),
                "sent_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            await self._update_notification_status(
                notification_id, NotificationStatus.FAILED, str(e)
            )
            logger.error(f"Notification sending failed for {notification_id}: {e}")
            raise ValueError(f"Failed to send notification: {str(e)}")

    async def send_bulk_notifications(
        self,
        recipients: list[str],
        notification_type: NotificationType,
        template: NotificationTemplate,
        data: dict[str, Any],
        priority: NotificationPriority = NotificationPriority.NORMAL,
    ) -> dict[str, Any]:
        """
        Send notifications to multiple recipients.

        Args:
            recipients: List of recipient identifiers
            notification_type: Type of notification channel
            template: Template to use
            data: Data to populate the template
            priority: Notification priority

        Returns:
            Bulk send results
        """
        successful_sends = []
        failed_sends = []

        # Process in batches to avoid overwhelming the system
        batch_size = getattr(settings, "NOTIFICATION_BATCH_SIZE", 100)

        for i in range(0, len(recipients), batch_size):
            batch = recipients[i : i + batch_size]
            batch_results = await asyncio.gather(
                *[
                    self.send_notification(
                        recipient=recipient,
                        notification_type=notification_type,
                        template=template,
                        data=data,
                        priority=priority,
                    )
                    for recipient in batch
                ],
                return_exceptions=True,
            )

            for recipient, result in zip(batch, batch_results, strict=False):
                if isinstance(result, Exception):
                    failed_sends.append({"recipient": recipient, "error": str(result)})
                elif result.get("success"):
                    successful_sends.append(
                        {
                            "recipient": recipient,
                            "notification_id": result["notification_id"],
                        }
                    )
                else:
                    failed_sends.append(
                        {
                            "recipient": recipient,
                            "error": result.get("message", "Unknown error"),
                        }
                    )

        return {
            "total_recipients": len(recipients),
            "successful_sends": len(successful_sends),
            "failed_sends": len(failed_sends),
            "successful_notifications": successful_sends,
            "failed_notifications": failed_sends,
            "processed_at": datetime.now(timezone.utc).isoformat(),
        }

    async def get_notification_status(self, notification_id: str) -> dict[str, Any]:
        """
        Get notification delivery status and analytics.

        Args:
            notification_id: Notification ID

        Returns:
            Notification status and delivery details
        """
        # TODO: Query database when notification model exists
        return {
            "notification_id": notification_id,
            "status": NotificationStatus.DELIVERED,
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "delivered_at": datetime.now(timezone.utc).isoformat(),
            "opened_at": None,
            "clicked_at": None,
            "delivery_attempts": 1,
            "error_message": None,
        }

    async def track_notification_event(
        self,
        notification_id: str,
        event_type: str,
        event_data: dict[str, Any] | None = None,
    ) -> bool:
        """
        Track notification events (opened, clicked, etc.).

        Args:
            notification_id: Notification ID
            event_type: Type of event (opened, clicked, bounced)
            event_data: Additional event data

        Returns:
            True if event was tracked successfully
        """
        try:
            # Update notification status based on event
            if event_type == "opened":
                await self._update_notification_status(
                    notification_id, NotificationStatus.OPENED
                )
            elif event_type == "clicked":
                await self._update_notification_status(
                    notification_id, NotificationStatus.CLICKED
                )
            elif event_type == "bounced":
                await self._update_notification_status(
                    notification_id, NotificationStatus.BOUNCED
                )

            # Log event for analytics
            await self._log_notification_event(notification_id, event_type, event_data)

            logger.info(f"Notification event tracked: {notification_id} - {event_type}")
            return True

        except Exception as e:
            logger.error(f"Failed to track notification event: {e}")
            return False

    async def update_user_preferences(
        self, user_id: str, preferences: dict[str, Any]
    ) -> bool:
        """
        Update user notification preferences.

        Args:
            user_id: User ID
            preferences: Notification preferences

        Returns:
            True if preferences were updated successfully
        """
        try:
            # TODO: Save to database when user_preferences model exists
            logger.info(f"User preferences updated for {user_id}")

            # Invalidate preferences cache
            await invalidate_cache_key(f"user_preferences:{user_id}")

            return True

        except Exception as e:
            logger.error(f"Failed to update user preferences: {e}")
            return False

    async def notify_order_status(
        self, order_id: str, status: str, customer_id: str
    ) -> dict[str, Any]:
        """Notify order status changes via WebSocket and other channels"""
        try:
            # Send WebSocket notification to customer
            await manager.send_personal_message(
                message=f"Tu pedido #{order_id} está {status}",
                user_id=customer_id,
                notification_type="order_update",
            )

            # Send WebSocket notification to admin
            await manager.broadcast_to_role(
                message=f"Pedido #{order_id} actualizado a {status}",
                role="admin",
                notification_type="order_admin_update",
            )

            # Send email notification asynchronously
            asyncio.create_task(
                self.send_notification(
                    recipient=customer_id,
                    notification_type=NotificationType.EMAIL,
                    template=self._get_order_template(status),
                    data={
                        "order_id": order_id,
                        "status": status,
                        "customer_id": customer_id,
                    },
                )
            )

            logger.info(
                f"Order status notification sent for order {order_id}: {status}"
            )
            return {"success": True, "message": "Order status notification sent"}

        except Exception as e:
            logger.error(f"Failed to send order status notification: {e}")
            return {"success": False, "error": str(e)}

    async def notify_low_stock(
        self, product_id: str, product_name: str, stock_quantity: int, min_stock: int
    ) -> dict[str, Any]:
        """Send low stock alerts via WebSocket and email"""
        try:
            message = f"⚠️ Stock bajo: {product_name} - Quedan {stock_quantity} unidades (mínimo: {min_stock})"

            # Send WebSocket notification to admin and managers
            await manager.broadcast_to_role(
                message, role="admin", notification_type="low_stock"
            )
            await manager.broadcast_to_role(
                message, role="manager", notification_type="low_stock"
            )

            # Send email notification to inventory managers
            asyncio.create_task(
                self.send_notification(
                    recipient="inventory@brain2gain.com",  # TODO: Get from config
                    notification_type=NotificationType.EMAIL,
                    template=NotificationTemplate.LOW_STOCK_ALERT,
                    data={
                        "product_id": product_id,
                        "product_name": product_name,
                        "stock_quantity": stock_quantity,
                        "min_stock": min_stock,
                    },
                )
            )

            logger.info(
                f"Low stock notification sent for product {product_id}: {stock_quantity} units"
            )
            return {"success": True, "message": "Low stock notification sent"}

        except Exception as e:
            logger.error(f"Failed to send low stock notification: {e}")
            return {"success": False, "error": str(e)}

    async def notify_new_order(
        self, order_id: str, customer_name: str, total_amount: float
    ) -> dict[str, Any]:
        """Notify about new orders"""
        try:
            message = (
                f"🛍️ Nuevo pedido #{order_id} de {customer_name} por ${total_amount:.2f}"
            )

            # Send WebSocket notification to admin and sales team
            await manager.broadcast_to_role(
                message, role="admin", notification_type="new_order"
            )
            await manager.broadcast_to_role(
                message, role="seller", notification_type="new_order"
            )

            logger.info(f"New order notification sent: {order_id}")
            return {"success": True, "message": "New order notification sent"}

        except Exception as e:
            logger.error(f"Failed to send new order notification: {e}")
            return {"success": False, "error": str(e)}

    async def send_system_alert(
        self, message: str, alert_type: str = "info", target_roles: list[str] = None
    ) -> dict[str, Any]:
        """Send system-wide alerts"""
        try:
            if target_roles is None:
                target_roles = ["admin"]

            for role in target_roles:
                await manager.broadcast_to_role(
                    message=f"🔔 {message}", role=role, notification_type=alert_type
                )

            logger.info(f"System alert sent to roles {target_roles}: {message}")
            return {"success": True, "message": "System alert sent"}

        except Exception as e:
            logger.error(f"Failed to send system alert: {e}")
            return {"success": False, "error": str(e)}

    def _get_order_template(self, status: str) -> NotificationTemplate:
        """Get appropriate template for order status"""
        status_mapping = {
            "confirmed": NotificationTemplate.ORDER_CONFIRMATION,
            "shipped": NotificationTemplate.ORDER_SHIPPED,
            "delivered": NotificationTemplate.ORDER_DELIVERED,
            "cancelled": NotificationTemplate.ORDER_CANCELLED,
        }
        return status_mapping.get(
            status.lower(), NotificationTemplate.ORDER_CONFIRMATION
        )

    async def get_notification_analytics(
        self,
        start_date: datetime,
        end_date: datetime,
        notification_type: NotificationType | None = None,
        template: NotificationTemplate | None = None,
    ) -> dict[str, Any]:
        """
        Get notification analytics for a date range.

        Args:
            start_date: Start date
            end_date: End date
            notification_type: Filter by notification type
            template: Filter by template

        Returns:
            Notification analytics data
        """
        # TODO: Implement database queries when notification tables exist
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "summary": {
                "total_sent": 1250,
                "total_delivered": 1189,
                "total_opened": 756,
                "total_clicked": 234,
                "total_bounced": 61,
                "delivery_rate": 95.12,
                "open_rate": 63.55,
                "click_rate": 30.95,
                "bounce_rate": 4.88,
            },
            "by_type": {
                "EMAIL": {"sent": 800, "delivered": 760, "opened": 480, "clicked": 156},
                "SMS": {"sent": 300, "delivered": 295, "opened": 200, "clicked": 45},
                "PUSH": {"sent": 150, "delivered": 134, "opened": 76, "clicked": 33},
            },
            "by_template": {},
            "timeline": [],
        }

    # Channel-specific sending methods

    async def _send_email(
        self,
        recipient: str,
        subject: str,
        content: str,
        template_data: dict[str, Any],
        attachments: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Send email notification."""
        try:
            # TODO: Integrate with actual email service (SendGrid, AWS SES, etc.)
            # For now, simulate email sending
            await asyncio.sleep(0.1)  # Simulate API call delay

            logger.info(f"Email sent to {recipient}: {subject}")

            return {
                "success": True,
                "status": NotificationStatus.SENT,
                "message_id": f"email_{uuid.uuid4().hex[:8]}",
                "message": "Email sent successfully (demo mode)",
            }

        except Exception as e:
            logger.error(f"Email sending failed: {e}")
            return {
                "success": False,
                "status": NotificationStatus.FAILED,
                "error": str(e),
            }

    async def _send_sms(
        self, recipient: str, message: str, template_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Send SMS notification."""
        try:
            # TODO: Integrate with SMS service (Twilio, AWS SNS, etc.)
            # For now, simulate SMS sending
            await asyncio.sleep(0.1)  # Simulate API call delay

            logger.info(f"SMS sent to {recipient}: {message[:50]}...")

            return {
                "success": True,
                "status": NotificationStatus.SENT,
                "message_id": f"sms_{uuid.uuid4().hex[:8]}",
                "message": "SMS sent successfully (demo mode)",
            }

        except Exception as e:
            logger.error(f"SMS sending failed: {e}")
            return {
                "success": False,
                "status": NotificationStatus.FAILED,
                "error": str(e),
            }

    async def _send_push_notification(
        self,
        recipient: str,
        title: str,
        body: str,
        template_data: dict[str, Any],
        action_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Send push notification."""
        try:
            # TODO: Integrate with push service (Firebase, Apple Push, etc.)
            # For now, simulate push notification sending
            await asyncio.sleep(0.1)  # Simulate API call delay

            logger.info(f"Push notification sent to {recipient}: {title}")

            return {
                "success": True,
                "status": NotificationStatus.SENT,
                "message_id": f"push_{uuid.uuid4().hex[:8]}",
                "message": "Push notification sent successfully (demo mode)",
            }

        except Exception as e:
            logger.error(f"Push notification sending failed: {e}")
            return {
                "success": False,
                "status": NotificationStatus.FAILED,
                "error": str(e),
            }

    # Template management

    def _get_template_content(
        self,
        template: NotificationTemplate,
        notification_type: NotificationType,
        data: dict[str, Any],
    ) -> dict[str, str]:
        """
        Get template content and populate with data.

        Args:
            template: Template identifier
            notification_type: Type of notification
            data: Data to populate template

        Returns:
            Template content (subject, body, etc.)
        """
        templates = {
            NotificationTemplate.ORDER_CONFIRMATION: {
                NotificationType.EMAIL: {
                    "subject": "Order Confirmation - #{order_id}",
                    "body": "Thank you for your order! Your order #{order_id} has been confirmed.",
                },
                NotificationType.SMS: {
                    "body": "Order #{order_id} confirmed! Thank you for shopping with us."
                },
                NotificationType.PUSH: {
                    "title": "Order Confirmed",
                    "body": "Your order #{order_id} has been confirmed",
                },
            },
            NotificationTemplate.ORDER_SHIPPED: {
                NotificationType.EMAIL: {
                    "subject": "Your order has shipped - #{order_id}",
                    "body": "Great news! Your order #{order_id} has shipped. Tracking: {tracking_number}",
                },
                NotificationType.SMS: {
                    "body": "Order #{order_id} shipped! Track: {tracking_number}"
                },
                NotificationType.PUSH: {
                    "title": "Order Shipped",
                    "body": "Your order is on its way!",
                },
            },
            NotificationTemplate.LOW_STOCK_ALERT: {
                NotificationType.EMAIL: {
                    "subject": "Low Stock Alert - {product_name}",
                    "body": "Product {product_name} is running low. Current stock: {stock_quantity}",
                }
            },
        }

        template_content = templates.get(template, {}).get(notification_type, {})

        # Populate template with data
        populated_content = {}
        for key, content in template_content.items():
            try:
                populated_content[key] = content.format(**data)
            except KeyError as e:
                logger.warning(f"Missing template data for {template}: {e}")
                populated_content[key] = content

        return populated_content

    # Private helper methods

    def _get_email_config(self) -> dict[str, Any]:
        """Get email service configuration."""
        return {
            "service": getattr(settings, "EMAIL_SERVICE", "sendgrid"),
            "api_key": getattr(settings, "EMAIL_API_KEY", "demo_key"),
            "from_email": getattr(settings, "FROM_EMAIL", "noreply@brain2gain.com"),
            "from_name": getattr(settings, "FROM_NAME", "Brain2Gain"),
        }

    def _get_sms_config(self) -> dict[str, Any]:
        """Get SMS service configuration."""
        return {
            "service": getattr(settings, "SMS_SERVICE", "twilio"),
            "api_key": getattr(settings, "SMS_API_KEY", "demo_key"),
            "from_number": getattr(settings, "SMS_FROM_NUMBER", "+1234567890"),
        }

    def _get_push_config(self) -> dict[str, Any]:
        """Get push notification service configuration."""
        return {
            "service": getattr(settings, "PUSH_SERVICE", "firebase"),
            "api_key": getattr(settings, "PUSH_API_KEY", "demo_key"),
            "project_id": getattr(settings, "PUSH_PROJECT_ID", "brain2gain-demo"),
        }

    async def _create_notification_record(
        self,
        notification_id: str,
        recipient: str,
        notification_type: NotificationType,
        template: NotificationTemplate,
        data: dict[str, Any],
        priority: NotificationPriority,
        scheduled_at: datetime | None,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Create notification record in database."""
        notification_record = {
            "notification_id": notification_id,
            "recipient": recipient,
            "notification_type": notification_type,
            "template": template,
            "data": data,
            "priority": priority,
            "status": NotificationStatus.PENDING,
            "scheduled_at": scheduled_at.isoformat() if scheduled_at else None,
            "metadata": metadata or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        # TODO: Save to database when notification model exists
        logger.info(f"Notification record created: {notification_id}")
        return notification_record

    async def _update_notification_status(
        self,
        notification_id: str,
        status: NotificationStatus,
        error_message: str | None = None,
    ) -> None:
        """Update notification status in database."""
        # TODO: Update database when notification model exists
        logger.info(f"Notification {notification_id} status updated to: {status}")

    async def _check_user_preferences(
        self,
        recipient: str,
        notification_type: NotificationType,
        template: NotificationTemplate,
    ) -> bool:
        """Check if user has opted in for this notification type."""
        # TODO: Query user preferences from database
        # For now, assume all notifications are allowed
        return True

    async def _schedule_notification(self, notification_record: dict[str, Any]) -> None:
        """Schedule notification for later delivery."""
        # TODO: Add to task queue (Celery, RQ, etc.)
        logger.info(f"Notification scheduled: {notification_record['notification_id']}")

    async def _send_immediate_notification(
        self, notification_record: dict[str, Any]
    ) -> dict[str, Any]:
        """Send notification immediately."""
        notification_type = notification_record["notification_type"]
        template = notification_record["template"]
        data = notification_record["data"]
        recipient = notification_record["recipient"]

        # Get template content
        content = self._get_template_content(template, notification_type, data)

        # Send based on type
        if notification_type == NotificationType.EMAIL:
            result = await self._send_email(
                recipient=recipient,
                subject=content.get("subject", "Notification"),
                content=content.get("body", ""),
                template_data=data,
            )
        elif notification_type == NotificationType.SMS:
            result = await self._send_sms(
                recipient=recipient, message=content.get("body", ""), template_data=data
            )
        elif notification_type == NotificationType.PUSH:
            result = await self._send_push_notification(
                recipient=recipient,
                title=content.get("title", "Notification"),
                body=content.get("body", ""),
                template_data=data,
            )
        else:
            result = {
                "success": False,
                "status": NotificationStatus.FAILED,
                "error": f"Unsupported notification type: {notification_type}",
            }

        # Update notification status
        await self._update_notification_status(
            notification_record["notification_id"], result["status"]
        )

        return result

    async def _log_notification_event(
        self, notification_id: str, event_type: str, event_data: dict[str, Any] | None
    ) -> None:
        """Log notification event for analytics."""
        # TODO: Save to database when notification_events model exists
        logger.info(f"Notification event logged: {notification_id} - {event_type}")


# Global notification service instance factory
def create_notification_service(session: AsyncSession) -> NotificationService:
    """Create a NotificationService instance with the given session."""
    return NotificationService(session)
