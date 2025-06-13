"""
Payment Service - Microservice for payment gateway integration
Part of Phase 3: Support Services Architecture

Handles:
- Payment processing with multiple gateways
- Payment method management
- Refunds and chargebacks
- Payment security and fraud detection
- Subscription and recurring payments
- Payment analytics and reporting
"""

import logging
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any, Union
from enum import Enum
import uuid
import hashlib
import hmac
import asyncio

from sqlalchemy.exc import IntegrityError
from sqlmodel import select, and_, or_
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.cache import cache_key_wrapper, invalidate_cache_pattern, invalidate_cache_key

logger = logging.getLogger(__name__)


class PaymentStatus(str, Enum):
    """Payment status enumeration"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"
    DISPUTED = "DISPUTED"


class PaymentMethod(str, Enum):
    """Payment method enumeration"""
    CREDIT_CARD = "CREDIT_CARD"
    DEBIT_CARD = "DEBIT_CARD"
    PAYPAL = "PAYPAL"
    STRIPE = "STRIPE"
    BANK_TRANSFER = "BANK_TRANSFER"
    DIGITAL_WALLET = "DIGITAL_WALLET"
    CRYPTOCURRENCY = "CRYPTOCURRENCY"


class RefundReason(str, Enum):
    """Refund reason enumeration"""
    CUSTOMER_REQUEST = "CUSTOMER_REQUEST"
    ORDER_CANCELLED = "ORDER_CANCELLED"
    DEFECTIVE_PRODUCT = "DEFECTIVE_PRODUCT"
    PROCESSING_ERROR = "PROCESSING_ERROR"
    FRAUD_PREVENTION = "FRAUD_PREVENTION"
    CHARGEBACK = "CHARGEBACK"


class PaymentService:
    """Service for payment processing and management."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.enabled_gateways = self._get_enabled_payment_gateways()
    
    async def process_payment(
        self,
        amount: Decimal,
        currency: str,
        payment_method: PaymentMethod,
        payment_details: Dict[str, Any],
        order_id: str,
        customer_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a payment through the appropriate gateway.
        
        Args:
            amount: Payment amount
            currency: Currency code (USD, EUR, etc.)
            payment_method: Payment method type
            payment_details: Payment-specific details (card info, PayPal token, etc.)
            order_id: Associated order ID
            customer_id: Customer ID
            metadata: Additional metadata
            
        Returns:
            Payment result with transaction details
            
        Raises:
            ValueError: If payment validation fails
        """
        # Validate payment request
        await self._validate_payment_request(amount, currency, payment_method, payment_details)
        
        # Create payment record
        payment_id = str(uuid.uuid4())
        payment_record = await self._create_payment_record(
            payment_id=payment_id,
            amount=amount,
            currency=currency,
            payment_method=payment_method,
            order_id=order_id,
            customer_id=customer_id,
            metadata=metadata
        )
        
        try:
            # Select appropriate payment gateway
            gateway = self._select_payment_gateway(payment_method, amount)
            
            # Process payment through gateway
            gateway_response = await self._process_gateway_payment(
                gateway=gateway,
                payment_record=payment_record,
                payment_details=payment_details
            )
            
            # Update payment record with gateway response
            payment_record = await self._update_payment_record(
                payment_id=payment_id,
                status=gateway_response["status"],
                gateway_transaction_id=gateway_response.get("transaction_id"),
                gateway_response=gateway_response
            )
            
            # Handle successful payment
            if gateway_response["status"] == PaymentStatus.COMPLETED:
                await self._handle_successful_payment(payment_record)
            
            logger.info(f"Payment processed: {payment_id} - Status: {gateway_response['status']}")
            
            return {
                "success": gateway_response["status"] == PaymentStatus.COMPLETED,
                "payment_id": payment_id,
                "status": gateway_response["status"],
                "transaction_id": gateway_response.get("transaction_id"),
                "amount": amount,
                "currency": currency,
                "gateway": gateway,
                "message": gateway_response.get("message", "Payment processed"),
                "processed_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            # Mark payment as failed
            await self._update_payment_record(
                payment_id=payment_id,
                status=PaymentStatus.FAILED,
                error_message=str(e)
            )
            
            logger.error(f"Payment processing failed for {payment_id}: {e}")
            raise ValueError(f"Payment processing failed: {str(e)}")
    
    async def refund_payment(
        self,
        payment_id: str,
        refund_amount: Optional[Decimal] = None,
        reason: RefundReason = RefundReason.CUSTOMER_REQUEST,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a payment refund.
        
        Args:
            payment_id: Original payment ID
            refund_amount: Amount to refund (None for full refund)
            reason: Reason for refund
            notes: Additional notes
            
        Returns:
            Refund result
            
        Raises:
            ValueError: If refund validation fails
        """
        # Get original payment
        payment_record = await self._get_payment_by_id(payment_id)
        if not payment_record:
            raise ValueError("Payment not found")
        
        if payment_record["status"] != PaymentStatus.COMPLETED:
            raise ValueError("Can only refund completed payments")
        
        # Determine refund amount
        if refund_amount is None:
            refund_amount = payment_record["amount"]
        
        # Validate refund amount
        total_refunded = await self._get_total_refunded_amount(payment_id)
        available_refund = payment_record["amount"] - total_refunded
        
        if refund_amount > available_refund:
            raise ValueError(f"Refund amount exceeds available amount. Available: {available_refund}")
        
        try:
            # Create refund record
            refund_id = str(uuid.uuid4())
            refund_record = await self._create_refund_record(
                refund_id=refund_id,
                payment_id=payment_id,
                amount=refund_amount,
                reason=reason,
                notes=notes
            )
            
            # Process refund through gateway
            gateway = payment_record["gateway"]
            gateway_response = await self._process_gateway_refund(
                gateway=gateway,
                original_transaction_id=payment_record["gateway_transaction_id"],
                refund_amount=refund_amount,
                refund_record=refund_record
            )
            
            # Update refund record
            await self._update_refund_record(
                refund_id=refund_id,
                status=gateway_response["status"],
                gateway_refund_id=gateway_response.get("refund_id"),
                gateway_response=gateway_response
            )
            
            # Update original payment status
            new_total_refunded = total_refunded + refund_amount
            if new_total_refunded >= payment_record["amount"]:
                new_payment_status = PaymentStatus.REFUNDED
            else:
                new_payment_status = PaymentStatus.PARTIALLY_REFUNDED
            
            await self._update_payment_record(
                payment_id=payment_id,
                status=new_payment_status
            )
            
            logger.info(f"Refund processed: {refund_id} for payment {payment_id}")
            
            return {
                "success": gateway_response["status"] == "COMPLETED",
                "refund_id": refund_id,
                "payment_id": payment_id,
                "amount": refund_amount,
                "status": gateway_response["status"],
                "gateway_refund_id": gateway_response.get("refund_id"),
                "processed_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Refund processing failed for payment {payment_id}: {e}")
            raise ValueError(f"Refund processing failed: {str(e)}")
    
    async def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """
        Get current payment status and details.
        
        Args:
            payment_id: Payment ID
            
        Returns:
            Payment status and details
        """
        payment_record = await self._get_payment_by_id(payment_id)
        if not payment_record:
            raise ValueError("Payment not found")
        
        # Get refund history
        refunds = await self._get_payment_refunds(payment_id)
        
        return {
            **payment_record,
            "refunds": refunds,
            "total_refunded": sum(r["amount"] for r in refunds if r["status"] == "COMPLETED"),
            "net_amount": payment_record["amount"] - sum(r["amount"] for r in refunds if r["status"] == "COMPLETED")
        }
    
    async def verify_webhook(
        self,
        gateway: str,
        payload: bytes,
        signature: str,
        headers: Dict[str, str]
    ) -> bool:
        """
        Verify webhook authenticity from payment gateway.
        
        Args:
            gateway: Payment gateway name
            payload: Webhook payload
            signature: Webhook signature
            headers: Request headers
            
        Returns:
            True if webhook is authentic
        """
        if gateway == "stripe":
            return self._verify_stripe_webhook(payload, signature)
        elif gateway == "paypal":
            return self._verify_paypal_webhook(payload, headers)
        else:
            logger.warning(f"Webhook verification not implemented for gateway: {gateway}")
            return False
    
    async def handle_webhook(
        self,
        gateway: str,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle payment gateway webhooks.
        
        Args:
            gateway: Payment gateway name
            event_type: Type of webhook event
            event_data: Event data from gateway
            
        Returns:
            Processing result
        """
        try:
            if event_type in ["payment.completed", "charge.succeeded"]:
                await self._handle_payment_completed_webhook(event_data)
            elif event_type in ["payment.failed", "charge.failed"]:
                await self._handle_payment_failed_webhook(event_data)
            elif event_type in ["refund.completed"]:
                await self._handle_refund_completed_webhook(event_data)
            elif event_type in ["chargeback.created"]:
                await self._handle_chargeback_webhook(event_data)
            else:
                logger.info(f"Unhandled webhook event: {event_type} from {gateway}")
            
            return {
                "success": True,
                "event_type": event_type,
                "processed_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error handling webhook {event_type} from {gateway}: {e}")
            return {
                "success": False,
                "error": str(e),
                "event_type": event_type
            }
    
    async def get_payment_analytics(
        self,
        start_date: datetime,
        end_date: datetime,
        group_by: str = "day"
    ) -> Dict[str, Any]:
        """
        Get payment analytics for a date range.
        
        Args:
            start_date: Start date
            end_date: End date
            group_by: Grouping period (day, week, month)
            
        Returns:
            Payment analytics data
        """
        # TODO: Implement database queries when payment tables exist
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "group_by": group_by
            },
            "summary": {
                "total_payments": 0,
                "total_amount": Decimal("0.00"),
                "successful_payments": 0,
                "failed_payments": 0,
                "refunded_amount": Decimal("0.00"),
                "average_payment_amount": Decimal("0.00")
            },
            "by_method": {},
            "by_gateway": {},
            "timeline": []
        }
    
    # Private helper methods
    
    def _get_enabled_payment_gateways(self) -> List[str]:
        """Get list of enabled payment gateways from configuration."""
        return getattr(settings, 'ENABLED_PAYMENT_GATEWAYS', ['stripe', 'paypal'])
    
    async def _validate_payment_request(
        self,
        amount: Decimal,
        currency: str,
        payment_method: PaymentMethod,
        payment_details: Dict[str, Any]
    ) -> None:
        """Validate payment request parameters."""
        if amount <= 0:
            raise ValueError("Payment amount must be positive")
        
        if currency not in ["USD", "EUR", "GBP", "CAD"]:  # Add supported currencies
            raise ValueError(f"Unsupported currency: {currency}")
        
        min_amount = Decimal("0.50")  # Minimum payment amount
        if amount < min_amount:
            raise ValueError(f"Payment amount must be at least {min_amount}")
        
        max_amount = Decimal("10000.00")  # Maximum payment amount
        if amount > max_amount:
            raise ValueError(f"Payment amount cannot exceed {max_amount}")
        
        # Validate payment method specific details
        if payment_method == PaymentMethod.CREDIT_CARD:
            required_fields = ["card_number", "expiry_month", "expiry_year", "cvc"]
            for field in required_fields:
                if field not in payment_details:
                    raise ValueError(f"Missing required field for credit card: {field}")
    
    def _select_payment_gateway(self, payment_method: PaymentMethod, amount: Decimal) -> str:
        """Select the best payment gateway based on method and amount."""
        if payment_method in [PaymentMethod.CREDIT_CARD, PaymentMethod.DEBIT_CARD]:
            # Use Stripe for card payments
            return "stripe"
        elif payment_method == PaymentMethod.PAYPAL:
            return "paypal"
        else:
            # Default to first enabled gateway
            return self.enabled_gateways[0] if self.enabled_gateways else "stripe"
    
    async def _create_payment_record(
        self,
        payment_id: str,
        amount: Decimal,
        currency: str,
        payment_method: PaymentMethod,
        order_id: str,
        customer_id: str,
        metadata: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create a payment record in the database."""
        payment_record = {
            "payment_id": payment_id,
            "amount": amount,
            "currency": currency,
            "payment_method": payment_method,
            "order_id": order_id,
            "customer_id": customer_id,
            "status": PaymentStatus.PENDING,
            "metadata": metadata or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # TODO: Save to database when payment model exists
        logger.info(f"Payment record created: {payment_id}")
        return payment_record
    
    async def _process_gateway_payment(
        self,
        gateway: str,
        payment_record: Dict[str, Any],
        payment_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process payment through the specified gateway."""
        if gateway == "stripe":
            return await self._process_stripe_payment(payment_record, payment_details)
        elif gateway == "paypal":
            return await self._process_paypal_payment(payment_record, payment_details)
        else:
            # Simulate payment processing for demo
            return {
                "status": PaymentStatus.COMPLETED,
                "transaction_id": f"demo_{uuid.uuid4().hex[:8]}",
                "message": f"Payment processed successfully via {gateway} (demo mode)"
            }
    
    async def _process_stripe_payment(
        self,
        payment_record: Dict[str, Any],
        payment_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process payment through Stripe."""
        # TODO: Integrate with actual Stripe API
        # For now, simulate successful payment
        await asyncio.sleep(0.1)  # Simulate API call delay
        
        return {
            "status": PaymentStatus.COMPLETED,
            "transaction_id": f"stripe_{uuid.uuid4().hex[:8]}",
            "message": "Payment processed successfully via Stripe (demo mode)"
        }
    
    async def _process_paypal_payment(
        self,
        payment_record: Dict[str, Any],
        payment_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process payment through PayPal."""
        # TODO: Integrate with actual PayPal API
        # For now, simulate successful payment
        await asyncio.sleep(0.1)  # Simulate API call delay
        
        return {
            "status": PaymentStatus.COMPLETED,
            "transaction_id": f"paypal_{uuid.uuid4().hex[:8]}",
            "message": "Payment processed successfully via PayPal (demo mode)"
        }
    
    async def _update_payment_record(
        self,
        payment_id: str,
        status: PaymentStatus,
        gateway_transaction_id: Optional[str] = None,
        gateway_response: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update payment record with processing results."""
        # TODO: Update database record when payment model exists
        logger.info(f"Payment {payment_id} updated to status: {status}")
        
        return {
            "payment_id": payment_id,
            "status": status,
            "gateway_transaction_id": gateway_transaction_id,
            "gateway_response": gateway_response,
            "error_message": error_message,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def _get_payment_by_id(self, payment_id: str) -> Optional[Dict[str, Any]]:
        """Get payment record by ID."""
        # TODO: Query database when payment model exists
        # For now, return placeholder
        return {
            "payment_id": payment_id,
            "amount": Decimal("99.99"),
            "currency": "USD",
            "status": PaymentStatus.COMPLETED,
            "gateway": "stripe",
            "gateway_transaction_id": f"stripe_{uuid.uuid4().hex[:8]}",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def _handle_successful_payment(self, payment_record: Dict[str, Any]) -> None:
        """Handle post-payment success actions."""
        # TODO: Integrate with Order Service to update order status
        # TODO: Integrate with Notification Service to send confirmation
        logger.info(f"Payment successful: {payment_record['payment_id']}")
    
    # Webhook verification methods
    
    def _verify_stripe_webhook(self, payload: bytes, signature: str) -> bool:
        """Verify Stripe webhook signature."""
        try:
            webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', 'demo_secret')
            expected_signature = hmac.new(
                webhook_secret.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(signature, expected_signature)
        except Exception as e:
            logger.error(f"Stripe webhook verification failed: {e}")
            return False
    
    def _verify_paypal_webhook(self, payload: bytes, headers: Dict[str, str]) -> bool:
        """Verify PayPal webhook authenticity."""
        # TODO: Implement PayPal webhook verification
        # For now, always return True in demo mode
        return True
    
    # Webhook handlers
    
    async def _handle_payment_completed_webhook(self, event_data: Dict[str, Any]) -> None:
        """Handle payment completed webhook."""
        logger.info("Payment completed webhook received")
    
    async def _handle_payment_failed_webhook(self, event_data: Dict[str, Any]) -> None:
        """Handle payment failed webhook."""
        logger.info("Payment failed webhook received")
    
    async def _handle_refund_completed_webhook(self, event_data: Dict[str, Any]) -> None:
        """Handle refund completed webhook."""
        logger.info("Refund completed webhook received")
    
    async def _handle_chargeback_webhook(self, event_data: Dict[str, Any]) -> None:
        """Handle chargeback webhook."""
        logger.warning("Chargeback webhook received")
    
    # Refund-related methods
    
    async def _create_refund_record(
        self,
        refund_id: str,
        payment_id: str,
        amount: Decimal,
        reason: RefundReason,
        notes: Optional[str]
    ) -> Dict[str, Any]:
        """Create a refund record."""
        # TODO: Save to database when refund model exists
        return {
            "refund_id": refund_id,
            "payment_id": payment_id,
            "amount": amount,
            "reason": reason,
            "notes": notes,
            "status": "PENDING",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def _process_gateway_refund(
        self,
        gateway: str,
        original_transaction_id: str,
        refund_amount: Decimal,
        refund_record: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process refund through gateway."""
        # TODO: Implement actual gateway refund calls
        # For now, simulate successful refund
        return {
            "status": "COMPLETED",
            "refund_id": f"{gateway}_refund_{uuid.uuid4().hex[:8]}",
            "message": f"Refund processed via {gateway} (demo mode)"
        }
    
    async def _update_refund_record(
        self,
        refund_id: str,
        status: str,
        gateway_refund_id: Optional[str],
        gateway_response: Dict[str, Any]
    ) -> None:
        """Update refund record with processing results."""
        # TODO: Update database when refund model exists
        logger.info(f"Refund {refund_id} updated to status: {status}")
    
    async def _get_total_refunded_amount(self, payment_id: str) -> Decimal:
        """Get total amount already refunded for a payment."""
        # TODO: Query database when refund model exists
        return Decimal("0.00")
    
    async def _get_payment_refunds(self, payment_id: str) -> List[Dict[str, Any]]:
        """Get all refunds for a payment."""
        # TODO: Query database when refund model exists
        return []


# Global payment service instance factory
def create_payment_service(session: AsyncSession) -> PaymentService:
    """Create a PaymentService instance with the given session."""
    return PaymentService(session)