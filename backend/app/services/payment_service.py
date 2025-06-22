# backend/app/services/payment_service.py
import logging
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from fastapi import HTTPException, status
from sqlmodel import Session, and_, func, select

from app.models import Order, Payment, PaymentStatus, Refund
from app.schemas.payment import (
    BankTransferResponse,
    PaymentFilters,
    PaymentMethodConfig,
    PaymentMethodsList,
    PaymentProcessResponse,
    PayPalPaymentResponse,
    StripePaymentResponse,
)
from app.services.paypal_service import PayPalService
from app.services.stripe_service import StripeService

logger = logging.getLogger(__name__)


class PaymentService:
    """Service for payment processing and management."""

    def __init__(self, session: Session):
        self.session = session
        self.stripe_service = StripeService(session)
        self.paypal_service = PayPalService(session)

    # ─── PAYMENT INITIATION ──────────────────────────────────────────────
    async def initiate_payment(
        self,
        order_id: uuid.UUID,
        payment_method: str,
        amount: Decimal
    ) -> dict[str, Any]:
        """
        Initiate payment for an order
        """
        # Create payment record
        payment = Payment(
            order_id=order_id,
            amount=amount,
            currency="MXN",
            payment_method=payment_method,
            status=PaymentStatus.PENDING
        )

        self.session.add(payment)
        self.session.commit()
        self.session.refresh(payment)

        # Initialize payment based on method
        if payment_method == "stripe":
            return await self._initiate_stripe_payment(payment)
        elif payment_method == "paypal":
            return await self._initiate_paypal_payment(payment)
        elif payment_method == "bank_transfer":
            return await self._initiate_bank_transfer(payment)
        else:
            raise ValueError(f"Unsupported payment method: {payment_method}")

    # ─── PAYMENT PROCESSING ──────────────────────────────────────────────
    async def process_stripe_payment(
        self,
        payment_id: uuid.UUID,
        payment_method_id: str,
        customer_id: str | None = None
    ) -> PaymentProcessResponse:
        """
        Process Stripe payment
        """
        payment = await self.get_payment_by_id(payment_id)
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )

        try:
            # TODO: Integrate with actual Stripe SDK
            # For now, simulate successful payment

            # Update payment record
            payment.status = PaymentStatus.CAPTURED
            payment.stripe_payment_intent_id = f"pi_mock_{uuid.uuid4().hex[:16]}"
            payment.captured_at = datetime.utcnow()
            payment.gateway_response = {
                "payment_method_id": payment_method_id,
                "customer_id": customer_id,
                "status": "succeeded"
            }

            self.session.add(payment)
            self.session.commit()

            # Create response
            stripe_response = StripePaymentResponse(
                success=True,
                payment_intent_id=payment.stripe_payment_intent_id,
                status="succeeded"
            )

            return PaymentProcessResponse(
                success=True,
                payment_id=payment_id,
                status=PaymentStatus.CAPTURED,
                message="Payment processed successfully",
                stripe_response=stripe_response
            )

        except Exception as e:
            # Update payment as failed
            payment.status = PaymentStatus.FAILED
            payment.failed_at = datetime.utcnow()
            payment.failure_reason = str(e)

            self.session.add(payment)
            self.session.commit()

            logger.error(f"Stripe payment failed for payment {payment_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Payment processing failed: {str(e)}"
            )

    async def process_paypal_payment(
        self,
        payment_id: uuid.UUID,
        paypal_order_id: str
    ) -> PaymentProcessResponse:
        """
        Process PayPal payment
        """
        payment = await self.get_payment_by_id(payment_id)
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )

        try:
            # TODO: Integrate with actual PayPal SDK
            # For now, simulate successful payment

            # Update payment record
            payment.status = PaymentStatus.CAPTURED
            payment.paypal_order_id = paypal_order_id
            payment.captured_at = datetime.utcnow()
            payment.gateway_response = {
                "paypal_order_id": paypal_order_id,
                "status": "completed"
            }

            self.session.add(payment)
            self.session.commit()

            # Create response
            paypal_response = PayPalPaymentResponse(
                success=True,
                order_id=paypal_order_id,
                status="completed"
            )

            return PaymentProcessResponse(
                success=True,
                payment_id=payment_id,
                status=PaymentStatus.CAPTURED,
                message="Payment processed successfully",
                paypal_response=paypal_response
            )

        except Exception as e:
            # Update payment as failed
            payment.status = PaymentStatus.FAILED
            payment.failed_at = datetime.utcnow()
            payment.failure_reason = str(e)

            self.session.add(payment)
            self.session.commit()

            logger.error(f"PayPal payment failed for payment {payment_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Payment processing failed: {str(e)}"
            )

    async def process_bank_transfer(
        self,
        payment_id: uuid.UUID
    ) -> PaymentProcessResponse:
        """
        Process bank transfer payment (manual confirmation required)
        """
        payment = await self.get_payment_by_id(payment_id)
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )

        # Bank transfers are pending until manually confirmed
        payment.status = PaymentStatus.PENDING
        payment.gateway_transaction_id = f"bt_ref_{uuid.uuid4().hex[:12].upper()}"

        self.session.add(payment)
        self.session.commit()

        # Create response with bank details
        bank_response = BankTransferResponse(
            success=True,
            reference_number=payment.gateway_transaction_id,
            bank_details={
                "bank_name": "Banco Nacional de México",
                "account_number": "1234567890",
                "clabe": "012345678901234567",
                "beneficiary": "Brain2Gain Mexico S.A. de C.V."
            },
            instructions=(
                f"Transfer ${payment.amount} MXN to the account above using "
                f"reference: {payment.gateway_transaction_id}"
            ),
            expiry_date=datetime.utcnow()
        )

        return PaymentProcessResponse(
            success=True,
            payment_id=payment_id,
            status=PaymentStatus.PENDING,
            message="Bank transfer details generated. Payment pending confirmation.",
            bank_transfer_response=bank_response,
            requires_user_action=True,
            next_step="Complete bank transfer using provided details"
        )

    # ─── PAYMENT RETRIEVAL ───────────────────────────────────────────────
    async def get_payment_by_id(self, payment_id: uuid.UUID) -> Payment | None:
        """Get payment by ID"""
        statement = select(Payment).where(Payment.payment_id == payment_id)
        result = self.session.exec(statement)
        return result.first()

    async def get_user_payments(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 10,
        filters: PaymentFilters | None = None
    ) -> list[Payment]:
        """Get user's payments"""
        # Join with orders to filter by user
        statement = (
            select(Payment)
            .join(Order)
            .where(Order.user_id == user_id)
        )

        # Apply filters
        if filters:
            if filters.status:
                statement = statement.where(Payment.status.in_(filters.status))
            if filters.payment_method:
                statement = statement.where(Payment.payment_method.in_(filters.payment_method))
            if filters.date_from:
                statement = statement.where(Payment.created_at >= filters.date_from)
            if filters.date_to:
                statement = statement.where(Payment.created_at <= filters.date_to)
            if filters.min_amount:
                statement = statement.where(Payment.amount >= filters.min_amount)
            if filters.max_amount:
                statement = statement.where(Payment.amount <= filters.max_amount)
            if filters.order_id:
                statement = statement.where(Payment.order_id == filters.order_id)

        # Apply pagination
        statement = statement.order_by(Payment.created_at.desc())
        statement = statement.offset((page - 1) * page_size).limit(page_size)

        result = self.session.exec(statement)
        return list(result)

    async def get_all_payments(
        self,
        page: int = 1,
        page_size: int = 20,
        filters: PaymentFilters | None = None
    ) -> list[Payment]:
        """Get all payments (admin)"""
        statement = select(Payment)

        # Apply filters
        if filters:
            if filters.status:
                statement = statement.where(Payment.status.in_(filters.status))
            if filters.payment_method:
                statement = statement.where(Payment.payment_method.in_(filters.payment_method))
            if filters.date_from:
                statement = statement.where(Payment.created_at >= filters.date_from)
            if filters.date_to:
                statement = statement.where(Payment.created_at <= filters.date_to)
            if filters.min_amount:
                statement = statement.where(Payment.amount >= filters.min_amount)
            if filters.max_amount:
                statement = statement.where(Payment.amount <= filters.max_amount)
            if filters.order_id:
                statement = statement.where(Payment.order_id == filters.order_id)

        # Apply pagination
        statement = statement.order_by(Payment.created_at.desc())
        statement = statement.offset((page - 1) * page_size).limit(page_size)

        result = self.session.exec(statement)
        return list(result)

    # ─── PAYMENT METHODS ──────────────────────────────────────────────────
    async def get_available_payment_methods(self) -> PaymentMethodsList:
        """Get available payment methods"""
        methods = [
            PaymentMethodConfig(
                method="stripe",
                enabled=True,
                display_name="Credit/Debit Card",
                description="Pay with your credit or debit card",
                icon_url="/static/icons/credit-card.svg",
                min_amount=Decimal("10"),
                max_amount=Decimal("50000"),
                processing_fee_percentage=Decimal("2.9"),
                fixed_fee=Decimal("0")
            ),
            PaymentMethodConfig(
                method="paypal",
                enabled=True,
                display_name="PayPal",
                description="Pay with your PayPal account",
                icon_url="/static/icons/paypal.svg",
                min_amount=Decimal("10"),
                max_amount=Decimal("25000"),
                processing_fee_percentage=Decimal("3.4"),
                fixed_fee=Decimal("0")
            ),
            PaymentMethodConfig(
                method="bank_transfer",
                enabled=True,
                display_name="Bank Transfer",
                description="Transfer money directly from your bank",
                icon_url="/static/icons/bank.svg",
                min_amount=Decimal("50"),
                max_amount=Decimal("100000"),
                processing_fee_percentage=Decimal("0"),
                fixed_fee=Decimal("15")
            )
        ]

        return PaymentMethodsList(
            methods=methods,
            default_method="stripe",
            currency="MXN"
        )

    # ─── REFUNDS ──────────────────────────────────────────────────────────
    async def create_refund(
        self,
        payment_id: uuid.UUID,
        amount: Decimal,
        reason: str
    ) -> Refund:
        """Create a refund"""
        payment = await self.get_payment_by_id(payment_id)
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )

        if payment.status != PaymentStatus.CAPTURED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only refund captured payments"
            )

        if amount > payment.amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Refund amount cannot exceed payment amount"
            )

        # Create refund record
        refund = Refund(
            payment_id=payment_id,
            order_id=payment.order_id,
            amount=amount,
            reason=reason,
            status="PENDING"
        )

        self.session.add(refund)
        self.session.commit()
        self.session.refresh(refund)

        # TODO: Process refund with payment gateway
        # For now, mark as completed
        refund.status = "COMPLETED"
        refund.processed_at = datetime.utcnow()

        # Update payment status if fully refunded
        total_refunded = self._calculate_total_refunded(payment_id)
        if total_refunded >= payment.amount:
            payment.status = PaymentStatus.REFUNDED

        self.session.add(refund)
        self.session.add(payment)
        self.session.commit()

        logger.info(f"Refund created for payment {payment_id}: ${amount}")
        return refund

    async def get_refund_by_id(self, refund_id: uuid.UUID) -> Refund | None:
        """Get refund by ID"""
        statement = select(Refund).where(Refund.refund_id == refund_id)
        result = self.session.exec(statement)
        return result.first()

    # ─── PAYMENT STATISTICS ──────────────────────────────────────────────
    async def get_payment_statistics(self) -> dict:
        """Get payment statistics for admin dashboard"""
        # Payment counts by status
        status_counts = {}
        for status in PaymentStatus:
            count_stmt = select(func.count(Payment.payment_id)).where(Payment.status == status)
            count = self.session.exec(count_stmt).first()
            status_counts[status.value] = count

        # Payment amounts
        total_stmt = select(func.sum(Payment.amount)).where(
            Payment.status == PaymentStatus.CAPTURED
        )
        total_amount = self.session.exec(total_stmt).first() or Decimal(0)

        # Refund amounts
        refund_stmt = select(func.sum(Refund.amount)).where(
            Refund.status == "COMPLETED"
        )
        total_refunds = self.session.exec(refund_stmt).first() or Decimal(0)

        # Payment method counts
        method_counts = {}
        methods = ["stripe", "paypal", "bank_transfer"]
        for method in methods:
            count_stmt = select(func.count(Payment.payment_id)).where(
                Payment.payment_method == method
            )
            count = self.session.exec(count_stmt).first()
            method_counts[method] = count

        # Average payment amount
        avg_stmt = select(func.avg(Payment.amount)).where(
            Payment.status == PaymentStatus.CAPTURED
        )
        avg_amount = self.session.exec(avg_stmt).first() or Decimal(0)

        # Conversion rate
        total_payments = sum(status_counts.values())
        successful_payments = status_counts.get("CAPTURED", 0)
        conversion_rate = (successful_payments / total_payments * 100) if total_payments > 0 else 0

        return {
            "total_payments": total_payments,
            "successful_payments": successful_payments,
            "failed_payments": status_counts.get("FAILED", 0),
            "pending_payments": status_counts.get("PENDING", 0),
            "total_amount": total_amount,
            "total_refunds": total_refunds,
            "net_revenue": total_amount - total_refunds,
            "stripe_payments": method_counts.get("stripe", 0),
            "paypal_payments": method_counts.get("paypal", 0),
            "bank_transfer_payments": method_counts.get("bank_transfer", 0),
            "average_payment_amount": avg_amount,
            "conversion_rate": float(conversion_rate)
        }

    # ─── WEBHOOK HANDLERS ─────────────────────────────────────────────────
    async def verify_stripe_webhook(self, body: bytes, signature: str) -> dict:
        """Verify Stripe webhook signature"""
        # TODO: Implement actual Stripe webhook verification
        # For now, return mock event
        return {
            "id": "evt_mock",
            "type": "payment_intent.succeeded",
            "data": {"object": {"id": "pi_mock"}}
        }

    async def verify_paypal_webhook(self, body: bytes, headers: dict) -> dict:
        """Verify PayPal webhook signature"""
        # TODO: Implement actual PayPal webhook verification
        # For now, return mock event
        return {
            "id": "evt_mock",
            "event_type": "PAYMENT.CAPTURE.COMPLETED",
            "resource": {"id": "paypal_mock"}
        }

    async def process_stripe_webhook(self, event: dict):
        """Process Stripe webhook event"""
        # TODO: Implement webhook processing
        logger.info(f"Processing Stripe webhook: {event.get('type')}")

    async def process_paypal_webhook(self, event: dict):
        """Process PayPal webhook event"""
        # TODO: Implement webhook processing
        logger.info(f"Processing PayPal webhook: {event.get('event_type')}")

    # ─── PRIVATE HELPER METHODS ──────────────────────────────────────────
    async def _initiate_stripe_payment(self, payment: Payment) -> dict[str, Any]:
        """Initialize Stripe payment"""
        try:
            # Create Stripe Payment Intent
            intent_data = await self.stripe_service.create_payment_intent(
                amount=payment.amount,
                currency=payment.currency.lower(),
                payment_id=payment.payment_id,
                metadata={
                    "order_id": str(payment.order_id),
                    "environment": "production" if payment.amount > 100 else "test"
                }
            )

            # Update payment record
            payment.stripe_payment_intent_id = intent_data["payment_intent_id"]
            payment.status = PaymentStatus.PENDING
            payment.gateway_response = intent_data

            self.session.add(payment)
            self.session.commit()

            logger.info(f"Created Stripe Payment Intent for payment {payment.payment_id}")

            return {
                "payment_intent_id": intent_data["payment_intent_id"],
                "client_secret": intent_data["client_secret"],
                "status": intent_data["status"]
            }

        except Exception as e:
            # Update payment as failed
            payment.status = PaymentStatus.FAILED
            payment.failed_at = datetime.utcnow()
            payment.failure_reason = str(e)

            self.session.add(payment)
            self.session.commit()

            logger.error(f"Failed to create Stripe Payment Intent: {str(e)}")
            raise

    async def _initiate_paypal_payment(self, payment: Payment) -> dict[str, Any]:
        """Initialize PayPal payment"""
        try:
            # Create PayPal Order
            order_data = await self.paypal_service.create_order(
                amount=payment.amount,
                currency=payment.currency,
                payment_id=payment.payment_id,
                return_url="https://brain2gain.com/checkout/success",
                cancel_url="https://brain2gain.com/checkout/cancel",
                metadata={
                    "order_id": str(payment.order_id),
                    "environment": "production" if payment.amount > 100 else "test"
                }
            )

            # Update payment record
            payment.paypal_order_id = order_data["order_id"]
            payment.status = PaymentStatus.PENDING
            payment.gateway_response = order_data

            self.session.add(payment)
            self.session.commit()

            logger.info(f"Created PayPal Order for payment {payment.payment_id}")

            return {
                "order_id": order_data["order_id"],
                "approval_url": order_data["approval_url"],
                "status": order_data["status"]
            }

        except Exception as e:
            # Update payment as failed
            payment.status = PaymentStatus.FAILED
            payment.failed_at = datetime.utcnow()
            payment.failure_reason = str(e)

            self.session.add(payment)
            self.session.commit()

            logger.error(f"Failed to create PayPal Order: {str(e)}")
            raise

    async def _initiate_bank_transfer(self, payment: Payment) -> dict[str, Any]:
        """Initialize bank transfer"""
        reference = f"BT-{uuid.uuid4().hex[:12].upper()}"

        payment.gateway_transaction_id = reference
        self.session.add(payment)
        self.session.commit()

        return {
            "reference_number": reference,
            "bank_details": {
                "bank_name": "Banco Nacional de México",
                "account_number": "1234567890",
                "clabe": "012345678901234567"
            }
        }

    def _calculate_total_refunded(self, payment_id: uuid.UUID) -> Decimal:
        """Calculate total amount refunded for a payment"""
        stmt = select(func.sum(Refund.amount)).where(
            and_(Refund.payment_id == payment_id, Refund.status == "COMPLETED")
        )
        result = self.session.exec(stmt).first()
        return result or Decimal(0)
