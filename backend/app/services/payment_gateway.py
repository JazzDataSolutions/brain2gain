import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from sqlmodel import Session

from app.models import Payment, PaymentStatus



class PaymentGateway(ABC):
    """Abstract payment gateway following Strategy pattern."""

    def __init__(self, session: Session):
        self.session = session

    @abstractmethod
    async def initiate_payment(self, payment: Payment) -> dict[str, Any]:
        """Initialize payment with external provider."""

    @abstractmethod
    async def process_payment(self, payment: Payment, **kwargs: Any) -> dict[str, Any]:
        """Process/capture the payment."""


class StripeGateway(PaymentGateway):
    def __init__(self, session: Session, stripe_service: Any):
        super().__init__(session)
        self.stripe_service = stripe_service

    async def initiate_payment(self, payment: Payment) -> dict[str, Any]:
        intent_data = await self.stripe_service.create_payment_intent(
            amount=payment.amount,
            currency=payment.currency.lower(),
            payment_id=payment.payment_id,
            metadata={"order_id": str(payment.order_id)},
        )
        payment.stripe_payment_intent_id = intent_data["payment_intent_id"]
        payment.gateway_response = intent_data
        return {
            "payment_intent_id": intent_data["payment_intent_id"],
            "client_secret": intent_data["client_secret"],
            "status": intent_data["status"],
        }

    async def process_payment(
        self, payment: Payment, payment_method_id: str, customer_id: str | None = None
    ) -> dict[str, Any]:
        payment.status = payment.status  # placeholder to keep logic simple
        payment.stripe_payment_intent_id = payment.stripe_payment_intent_id or f"pi_{uuid.uuid4().hex[:16]}"
        payment.captured_at = payment.captured_at or payment.created_at

        payment.gateway_response = {
            "payment_method_id": payment_method_id,
            "customer_id": customer_id,
            "status": "succeeded",
        }
        return {
            "success": True,
            "payment_id": payment.payment_id,
            "status": payment.gateway_response["status"],
        }


class PayPalGateway(PaymentGateway):
    def __init__(self, session: Session, paypal_service: Any):
        super().__init__(session)
        self.paypal_service = paypal_service

    async def initiate_payment(self, payment: Payment) -> dict[str, Any]:
        order_data = await self.paypal_service.create_order(
            amount=payment.amount,
            currency=payment.currency,
            payment_id=payment.payment_id,
            return_url="https://brain2gain.com/checkout/success",
            cancel_url="https://brain2gain.com/checkout/cancel",
            metadata={"order_id": str(payment.order_id)},
        )
        payment.paypal_order_id = order_data["order_id"]
        payment.gateway_response = order_data
        return {
            "order_id": order_data["order_id"],
            "approval_url": order_data["approval_url"],
            "status": order_data["status"],
        }


    async def process_payment(
        self, payment: Payment, paypal_order_id: str
    ) -> dict[str, Any]:
        payment.paypal_order_id = paypal_order_id
        payment.status = PaymentStatus.CAPTURED
        payment.captured_at = payment.captured_at or datetime.utcnow()
        payment.gateway_response = {
            "paypal_order_id": paypal_order_id,
            "status": "completed",
        }
        return {
            "success": True,
            "payment_id": payment.payment_id,
            "status": payment.gateway_response["status"],
        }


class BankTransferGateway(PaymentGateway):
    async def initiate_payment(self, payment: Payment) -> dict[str, Any]:
        reference = f"BT-{uuid.uuid4().hex[:12].upper()}"
        payment.gateway_transaction_id = reference
        return {
            "reference_number": reference,
            "bank_details": {
                "bank_name": "Banco Nacional de México",
                "account_number": "1234567890",
                "clabe": "012345678901234567",
            },
        }

    async def process_payment(self, payment: Payment) -> dict[str, Any]:
        payment.status = payment.status
        payment.captured_at = None
        return {"success": True, "payment_id": payment.payment_id, "status": "pending"}
