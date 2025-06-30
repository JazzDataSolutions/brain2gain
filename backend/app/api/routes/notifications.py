"""
Notifications API Routes - Email delivery and notification management
Part of Phase 3: Production Deployment Infrastructure

Endpoints:
- POST /notifications/send-email - Send single email
- POST /notifications/send-bulk-emails - Send multiple emails
- POST /notifications/order-confirmation - Send order confirmation
- POST /notifications/order-shipped - Send shipping notification
- POST /notifications/order-delivered - Send delivery notification
- POST /notifications/password-reset - Send password reset email
- POST /notifications/welcome - Send welcome email
- GET /notifications/test-email - Send test email
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from app.api.deps import get_current_active_superuser
from app.core.config import settings
from app.models import User
from app.services.email_delivery_service import (
    EmailDeliveryResult,
    EmailPriority,
    EmailRequest,
    email_delivery_service,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class SendEmailRequest(BaseModel):
    """Request model for sending email"""

    to: EmailStr
    subject: str
    template_name: str | None = None
    template_data: dict[str, Any] | None = None
    html_content: str | None = None
    priority: EmailPriority = EmailPriority.NORMAL


class BulkEmailRequest(BaseModel):
    """Request model for sending bulk emails"""

    emails: list[SendEmailRequest]
    batch_size: int = 10
    delay_between_batches: float = 1.0


class OrderEmailRequest(BaseModel):
    """Request model for order-related emails"""

    email: EmailStr
    order_id: str
    customer_name: str
    order_total: float
    items: list[dict[str, Any]]
    shipping_address: dict[str, str]
    tracking_number: str | None = None


class PasswordResetEmailRequest(BaseModel):
    """Request model for password reset email"""

    email: EmailStr
    reset_token: str
    user_name: str


class WelcomeEmailRequest(BaseModel):
    """Request model for welcome email"""

    email: EmailStr
    user_name: str
    temporary_password: str | None = None


@router.post("/send-email", response_model=EmailDeliveryResult)
async def send_email(
    request: SendEmailRequest,
    current_user: User = Depends(get_current_active_superuser),
) -> EmailDeliveryResult:
    """
    Send a single email using template or HTML content

    Requires superuser permissions for security.
    """
    try:
        email_request = EmailRequest(
            to=request.to,
            subject=request.subject,
            template_name=request.template_name,
            template_data=request.template_data,
            html_content=request.html_content,
            priority=request.priority,
        )

        result = await email_delivery_service.send_email(email_request)

        logger.info(f"Email sent to {request.to} by admin {current_user.email}")
        return result

    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}",
        )


@router.post("/send-bulk-emails", response_model=list[EmailDeliveryResult])
async def send_bulk_emails(
    request: BulkEmailRequest,
    current_user: User = Depends(get_current_active_superuser),
) -> list[EmailDeliveryResult]:
    """
    Send multiple emails in batches

    Requires superuser permissions for security.
    """
    try:
        email_requests = [
            EmailRequest(
                to=email.to,
                subject=email.subject,
                template_name=email.template_name,
                template_data=email.template_data,
                html_content=email.html_content,
                priority=email.priority,
            )
            for email in request.emails
        ]

        results = await email_delivery_service.send_bulk_emails(
            email_requests,
            batch_size=request.batch_size,
            delay_between_batches=request.delay_between_batches,
        )

        successful_count = sum(1 for result in results if result.success)
        logger.info(
            f"Bulk email completed: {successful_count}/{len(results)} successful "
            f"by admin {current_user.email}"
        )

        return results

    except Exception as e:
        logger.error(f"Failed to send bulk emails: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send bulk emails: {str(e)}",
        )


@router.post("/order-confirmation", response_model=EmailDeliveryResult)
async def send_order_confirmation(
    request: OrderEmailRequest,
) -> EmailDeliveryResult:
    """
    Send order confirmation email

    Public endpoint for order processing system.
    """
    try:
        order_data = {
            "order_id": request.order_id,
            "customer_name": request.customer_name,
            "order_total": request.order_total,
            "items": request.items,
            "shipping_address": request.shipping_address,
            "order_date": "2025-06-30",  # This should come from the actual order
            "company_name": settings.PROJECT_NAME,
            "company_website": settings.FRONTEND_HOST,
        }

        result = await email_delivery_service.send_order_confirmation(
            request.email, order_data
        )

        logger.info(
            f"Order confirmation sent for order {request.order_id} to {request.email}"
        )
        return result

    except Exception as e:
        logger.error(f"Failed to send order confirmation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send order confirmation: {str(e)}",
        )


@router.post("/order-shipped", response_model=EmailDeliveryResult)
async def send_order_shipped(
    request: OrderEmailRequest,
) -> EmailDeliveryResult:
    """
    Send order shipped notification

    Public endpoint for fulfillment system.
    """
    try:
        order_data = {
            "order_id": request.order_id,
            "customer_name": request.customer_name,
            "tracking_number": request.tracking_number,
            "shipping_address": request.shipping_address,
            "shipped_date": "2025-06-30",  # This should come from the actual shipment
            "company_name": settings.PROJECT_NAME,
            "company_website": settings.FRONTEND_HOST,
        }

        result = await email_delivery_service.send_order_shipped(
            request.email, order_data
        )

        logger.info(
            f"Order shipped notification sent for order {request.order_id} to {request.email}"
        )
        return result

    except Exception as e:
        logger.error(f"Failed to send order shipped notification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send order shipped notification: {str(e)}",
        )


@router.post("/order-delivered", response_model=EmailDeliveryResult)
async def send_order_delivered(
    request: OrderEmailRequest,
) -> EmailDeliveryResult:
    """
    Send order delivered notification

    Public endpoint for delivery confirmation system.
    """
    try:
        order_data = {
            "order_id": request.order_id,
            "customer_name": request.customer_name,
            "delivered_date": "2025-06-30",  # This should come from the actual delivery
            "company_name": settings.PROJECT_NAME,
            "company_website": settings.FRONTEND_HOST,
        }

        result = await email_delivery_service.send_order_delivered(
            request.email, order_data
        )

        logger.info(
            f"Order delivered notification sent for order {request.order_id} to {request.email}"
        )
        return result

    except Exception as e:
        logger.error(f"Failed to send order delivered notification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send order delivered notification: {str(e)}",
        )


@router.post("/password-reset", response_model=EmailDeliveryResult)
async def send_password_reset_email(
    request: PasswordResetEmailRequest,
) -> EmailDeliveryResult:
    """
    Send password reset email

    Public endpoint for authentication system.
    """
    try:
        reset_data = {
            "user_name": request.user_name,
            "reset_link": f"{settings.FRONTEND_HOST}/reset-password?token={request.reset_token}",
            "reset_token": request.reset_token,
            "expiry_hours": settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS,
            "company_name": settings.PROJECT_NAME,
            "company_website": settings.FRONTEND_HOST,
        }

        result = await email_delivery_service.send_password_reset(
            request.email, reset_data
        )

        logger.info(f"Password reset email sent to {request.email}")
        return result

    except Exception as e:
        logger.error(f"Failed to send password reset email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send password reset email: {str(e)}",
        )


@router.post("/welcome", response_model=EmailDeliveryResult)
async def send_welcome_email(
    request: WelcomeEmailRequest,
) -> EmailDeliveryResult:
    """
    Send welcome email for new users

    Public endpoint for user registration system.
    """
    try:
        user_data = {
            "user_name": request.user_name,
            "login_link": f"{settings.FRONTEND_HOST}/login",
            "temporary_password": request.temporary_password,
            "company_name": settings.PROJECT_NAME,
            "company_website": settings.FRONTEND_HOST,
            "support_email": settings.EMAILS_FROM_EMAIL,
        }

        result = await email_delivery_service.send_welcome_email(
            request.email, user_data
        )

        logger.info(f"Welcome email sent to {request.email}")
        return result

    except Exception as e:
        logger.error(f"Failed to send welcome email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send welcome email: {str(e)}",
        )


@router.get("/test-email", response_model=EmailDeliveryResult)
async def send_test_email(
    email_to: EmailStr,
    current_user: User = Depends(get_current_active_superuser),
) -> EmailDeliveryResult:
    """
    Send a test email to verify email delivery configuration

    Requires superuser permissions.
    """
    try:
        test_data = {
            "test_message": "This is a test email from Brain2Gain notification service",
            "sent_by": current_user.email,
            "sent_at": "2025-06-30",
            "company_name": settings.PROJECT_NAME,
            "company_website": settings.FRONTEND_HOST,
        }

        email_request = EmailRequest(
            to=email_to,
            subject=f"Test Email from {settings.PROJECT_NAME}",
            template_name="test_email.mjml",
            template_data=test_data,
            priority=EmailPriority.NORMAL,
        )

        result = await email_delivery_service.send_email(email_request)

        logger.info(f"Test email sent to {email_to} by admin {current_user.email}")
        return result

    except Exception as e:
        logger.error(f"Failed to send test email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send test email: {str(e)}",
        )
