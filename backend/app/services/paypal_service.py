# backend/app/services/paypal_service.py
"""
PayPal Payment Gateway Integration Service
Handles all PayPal-related payment operations for Brain2Gain
"""

import base64
import logging
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

import aiohttp
from fastapi import HTTPException, status
from sqlmodel import Session

from app.core.config import settings
from app.models import Payment, PaymentStatus

logger = logging.getLogger(__name__)


class PayPalService:
    """Service for PayPal payment processing."""

    def __init__(self, session: Session):
        self.session = session
        self.base_url = self._get_base_url()
        self.client_id = settings.PAYPAL_CLIENT_ID
        self.client_secret = settings.PAYPAL_CLIENT_SECRET
        self._access_token = None
        self._token_expires_at = None

    def _get_base_url(self) -> str:
        """Get PayPal API base URL based on environment"""
        if settings.PAYPAL_MODE == "live":
            return "https://api-m.paypal.com"
        else:
            return "https://api-m.sandbox.paypal.com"

    # ─── AUTHENTICATION ──────────────────────────────────────────────────
    async def _get_access_token(self) -> str:
        """
        Get PayPal access token for API calls
        
        Returns:
            Valid access token string
        """
        # Check if current token is still valid
        if (self._access_token and self._token_expires_at and
            datetime.utcnow() < self._token_expires_at):
            return self._access_token

        try:
            # Prepare authentication
            auth_string = f"{self.client_id}:{self.client_secret}"
            auth_bytes = auth_string.encode('ascii')
            auth_b64 = base64.b64encode(auth_bytes).decode('ascii')

            headers = {
                "Accept": "application/json",
                "Accept-Language": "en_US",
                "Authorization": f"Basic {auth_b64}",
                "Content-Type": "application/x-www-form-urlencoded"
            }

            data = "grant_type=client_credentials"

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/v1/oauth2/token",
                    headers=headers,
                    data=data
                ) as response:

                    if response.status != 200:
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="PayPal authentication failed"
                        )

                    token_data = await response.json()

                    self._access_token = token_data["access_token"]
                    expires_in = token_data.get("expires_in", 3600)  # Default 1 hour
                    self._token_expires_at = datetime.utcnow().timestamp() + expires_in - 60  # 1 min buffer

                    logger.info("Successfully obtained PayPal access token")
                    return self._access_token

        except Exception as e:
            logger.error(f"PayPal authentication error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Payment processor authentication failed"
            )

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: dict | None = None,
        headers: dict | None = None
    ) -> dict[str, Any]:
        """
        Make authenticated request to PayPal API
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            data: Request data
            headers: Additional headers
        
        Returns:
            API response data
        """
        access_token = await self._get_access_token()

        request_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
            "PayPal-Request-Id": str(uuid.uuid4()),  # Idempotency key
        }

        if headers:
            request_headers.update(headers)

        url = f"{self.base_url}{endpoint}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method,
                    url,
                    headers=request_headers,
                    json=data if data else None
                ) as response:

                    response_data = await response.json()

                    if response.status >= 400:
                        error_detail = response_data.get("details", [{}])[0].get("description", "Unknown PayPal error")
                        logger.error(f"PayPal API error: {response.status} - {error_detail}")
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"PayPal error: {error_detail}"
                        )

                    return response_data

        except aiohttp.ClientError as e:
            logger.error(f"PayPal connection error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Payment processor temporarily unavailable"
            )
        except Exception as e:
            logger.error(f"PayPal request error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Payment processing failed"
            )

    # ─── ORDER OPERATIONS ─────────────────────────────────────────────────
    async def create_order(
        self,
        amount: Decimal,
        currency: str = "MXN",
        payment_id: uuid.UUID = None,
        return_url: str = None,
        cancel_url: str = None,
        metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Create a PayPal Order
        
        Args:
            amount: Payment amount
            currency: Currency code
            payment_id: Internal payment ID for tracking
            return_url: URL to redirect after successful payment
            cancel_url: URL to redirect after cancelled payment
            metadata: Additional metadata
        
        Returns:
            Dict containing order details and approval URL
        """
        try:
            order_data = {
                "intent": "CAPTURE",
                "purchase_units": [
                    {
                        "amount": {
                            "currency_code": currency,
                            "value": str(amount)
                        },
                        "custom_id": str(payment_id) if payment_id else None,
                        "description": "Brain2Gain Purchase",
                        "soft_descriptor": "BRAIN2GAIN"
                    }
                ],
                "application_context": {
                    "brand_name": "Brain2Gain",
                    "landing_page": "NO_PREFERENCE",
                    "user_action": "PAY_NOW",
                    "payment_method": {
                        "payer_selected": "PAYPAL",
                        "payee_preferred": "IMMEDIATE_PAYMENT_REQUIRED"
                    }
                }
            }

            if return_url and cancel_url:
                order_data["application_context"]["return_url"] = return_url
                order_data["application_context"]["cancel_url"] = cancel_url

            response = await self._make_request("POST", "/v2/checkout/orders", order_data)

            # Extract approval URL
            approval_url = None
            for link in response.get("links", []):
                if link.get("rel") == "approve":
                    approval_url = link.get("href")
                    break

            logger.info(f"Created PayPal Order: {response['id']} for amount: {amount} {currency}")

            return {
                "order_id": response["id"],
                "status": response["status"],
                "approval_url": approval_url,
                "amount": amount,
                "currency": currency,
                "created_time": response.get("create_time")
            }

        except Exception as e:
            logger.error(f"Error creating PayPal order: {str(e)}")
            raise

    async def capture_order(self, order_id: str) -> dict[str, Any]:
        """
        Capture (complete) a PayPal Order
        
        Args:
            order_id: PayPal Order ID
        
        Returns:
            Dict containing capture details
        """
        try:
            response = await self._make_request("POST", f"/v2/checkout/orders/{order_id}/capture")

            logger.info(f"Captured PayPal Order: {order_id}")

            # Extract capture details
            capture = None
            purchase_units = response.get("purchase_units", [])
            if purchase_units:
                captures = purchase_units[0].get("payments", {}).get("captures", [])
                if captures:
                    capture = captures[0]

            return {
                "order_id": response["id"],
                "status": response["status"],
                "capture_id": capture.get("id") if capture else None,
                "amount": capture.get("amount", {}).get("value") if capture else None,
                "currency": capture.get("amount", {}).get("currency_code") if capture else None,
                "capture_status": capture.get("status") if capture else None,
                "create_time": response.get("create_time"),
                "update_time": response.get("update_time")
            }

        except Exception as e:
            logger.error(f"Error capturing PayPal order: {str(e)}")
            raise

    async def get_order(self, order_id: str) -> dict[str, Any]:
        """
        Retrieve PayPal Order details
        
        Args:
            order_id: PayPal Order ID
        
        Returns:
            Dict containing order details
        """
        try:
            response = await self._make_request("GET", f"/v2/checkout/orders/{order_id}")

            return {
                "order_id": response["id"],
                "status": response["status"],
                "intent": response["intent"],
                "create_time": response.get("create_time"),
                "update_time": response.get("update_time"),
                "purchase_units": response.get("purchase_units", [])
            }

        except Exception as e:
            logger.error(f"Error retrieving PayPal order: {str(e)}")
            raise

    # ─── REFUND OPERATIONS ────────────────────────────────────────────────
    async def create_refund(
        self,
        capture_id: str,
        amount: Decimal | None = None,
        currency: str = "MXN",
        note: str = None,
        invoice_id: str = None
    ) -> dict[str, Any]:
        """
        Create a refund for a PayPal capture
        
        Args:
            capture_id: PayPal Capture ID
            amount: Refund amount (if partial)
            currency: Currency code
            note: Refund note
            invoice_id: Invoice ID for tracking
        
        Returns:
            Dict containing refund details
        """
        try:
            refund_data = {}

            if amount:
                refund_data["amount"] = {
                    "value": str(amount),
                    "currency_code": currency
                }

            if note:
                refund_data["note_to_payer"] = note

            if invoice_id:
                refund_data["invoice_id"] = invoice_id

            response = await self._make_request("POST", f"/v2/payments/captures/{capture_id}/refund", refund_data)

            logger.info(f"Created PayPal Refund: {response['id']} for capture: {capture_id}")

            return {
                "refund_id": response["id"],
                "capture_id": capture_id,
                "status": response["status"],
                "amount": response.get("amount", {}).get("value"),
                "currency": response.get("amount", {}).get("currency_code"),
                "create_time": response.get("create_time"),
                "update_time": response.get("update_time")
            }

        except Exception as e:
            logger.error(f"Error creating PayPal refund: {str(e)}")
            raise

    # ─── WEBHOOK PROCESSING ───────────────────────────────────────────────
    async def verify_webhook(self, headers: dict[str, str], body: str) -> bool:
        """
        Verify PayPal webhook signature
        
        Args:
            headers: Request headers
            body: Raw request body
        
        Returns:
            True if webhook is valid
        """
        try:
            # PayPal webhook verification process
            # This is a simplified version - in production, implement full verification

            auth_algo = headers.get("PAYPAL-AUTH-ALGO")
            transmission_id = headers.get("PAYPAL-TRANSMISSION-ID")
            cert_id = headers.get("PAYPAL-CERT-ID")
            transmission_sig = headers.get("PAYPAL-TRANSMISSION-SIG")
            transmission_time = headers.get("PAYPAL-TRANSMISSION-TIME")

            if not all([auth_algo, transmission_id, cert_id, transmission_sig, transmission_time]):
                return False

            # In production, verify the webhook signature using PayPal's public certificate
            # For now, return True if all required headers are present
            logger.info(f"PayPal webhook verification: {transmission_id}")
            return True

        except Exception as e:
            logger.error(f"PayPal webhook verification error: {str(e)}")
            return False

    async def process_webhook(self, webhook_data: dict[str, Any]) -> dict[str, Any]:
        """
        Process PayPal webhook events
        
        Args:
            webhook_data: Webhook payload
        
        Returns:
            Dict containing processed event information
        """
        try:
            event_type = webhook_data.get("event_type")
            resource = webhook_data.get("resource", {})

            logger.info(f"Processing PayPal webhook: {event_type}")

            # Handle different event types
            if event_type == "CHECKOUT.ORDER.APPROVED":
                await self._handle_order_approved(resource)
            elif event_type == "PAYMENT.CAPTURE.COMPLETED":
                await self._handle_payment_completed(resource)
            elif event_type == "PAYMENT.CAPTURE.DENIED":
                await self._handle_payment_denied(resource)
            elif event_type == "CUSTOMER.DISPUTE.CREATED":
                await self._handle_dispute_created(resource)

            return {
                "event_id": webhook_data.get("id"),
                "event_type": event_type,
                "processed": True
            }

        except Exception as e:
            logger.error(f"Error processing PayPal webhook: {str(e)}")
            raise

    # ─── PRIVATE METHODS ──────────────────────────────────────────────────
    async def _handle_order_approved(self, order_data: dict[str, Any]) -> None:
        """Handle order approved webhook"""
        order_id = order_data.get("id")
        logger.info(f"PayPal Order approved: {order_id}")

        # Extract payment ID from custom_id if available
        purchase_units = order_data.get("purchase_units", [])
        if purchase_units:
            custom_id = purchase_units[0].get("custom_id")
            if custom_id:
                try:
                    payment_id = uuid.UUID(custom_id)
                    payment = self.session.get(Payment, payment_id)
                    if payment:
                        payment.status = PaymentStatus.AUTHORIZED
                        payment.authorized_at = datetime.utcnow()
                        payment.paypal_order_id = order_id
                        payment.gateway_response = order_data

                        self.session.add(payment)
                        self.session.commit()

                        logger.info(f"Updated payment {payment_id} status to AUTHORIZED")
                except Exception as e:
                    logger.error(f"Failed to update payment status: {str(e)}")

    async def _handle_payment_completed(self, capture_data: dict[str, Any]) -> None:
        """Handle payment completed webhook"""
        capture_id = capture_data.get("id")
        logger.info(f"PayPal Payment completed: {capture_id}")

        # Find payment by PayPal order ID
        # This would require additional logic to link capture to payment

    async def _handle_payment_denied(self, capture_data: dict[str, Any]) -> None:
        """Handle payment denied webhook"""
        capture_id = capture_data.get("id")
        logger.info(f"PayPal Payment denied: {capture_id}")

    async def _handle_dispute_created(self, dispute_data: dict[str, Any]) -> None:
        """Handle dispute created webhook"""
        dispute_id = dispute_data.get("dispute_id")
        logger.warning(f"PayPal Dispute created: {dispute_id}")
        # TODO: Implement dispute handling logic
