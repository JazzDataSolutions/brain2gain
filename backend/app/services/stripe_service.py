# backend/app/services/stripe_service.py
"""
Stripe Payment Gateway Integration Service
Handles all Stripe-related payment operations for Brain2Gain
"""

import logging
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

import stripe
from fastapi import HTTPException, status
from sqlmodel import Session

from app.core.config import settings
from app.models import Payment, PaymentStatus

logger = logging.getLogger(__name__)

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:
    """Service for Stripe payment processing."""

    def __init__(self, session: Session):
        self.session = session

    # ─── PAYMENT INTENT OPERATIONS ───────────────────────────────────────
    async def create_payment_intent(
        self,
        amount: Decimal,
        currency: str = "mxn",
        payment_id: uuid.UUID = None,
        customer_email: str = None,
        metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Create a Stripe Payment Intent
        
        Args:
            amount: Payment amount in smallest currency unit (centavos for MXN)
            currency: Currency code (default: mxn)
            payment_id: Internal payment ID for tracking
            customer_email: Customer email for receipt
            metadata: Additional metadata to store with the payment
        
        Returns:
            Dict containing payment intent details
        """
        try:
            # Convert decimal amount to cents/centavos
            amount_cents = int(amount * 100)

            # Prepare metadata
            intent_metadata = {
                "brain2gain_payment_id": str(payment_id) if payment_id else "",
                "platform": "brain2gain",
                "environment": settings.ENVIRONMENT
            }
            if metadata:
                intent_metadata.update(metadata)

            # Create payment intent
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency.lower(),
                metadata=intent_metadata,
                receipt_email=customer_email,
                automatic_payment_methods={
                    'enabled': True,
                },
                # Enable setup for future payments (optional)
                setup_future_usage='off_session' if customer_email else None,
            )

            logger.info(f"Created Stripe Payment Intent: {intent.id} for amount: {amount} {currency}")

            return {
                "payment_intent_id": intent.id,
                "client_secret": intent.client_secret,
                "status": intent.status,
                "amount": amount,
                "currency": currency,
                "created": intent.created
            }

        except stripe.error.CardError as e:
            logger.error(f"Stripe Card Error: {e.user_message}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Card error: {e.user_message}"
            )
        except stripe.error.RateLimitError as e:
            logger.error(f"Stripe Rate Limit Error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests to payment processor"
            )
        except stripe.error.InvalidRequestError as e:
            logger.error(f"Stripe Invalid Request: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid payment request: {str(e)}"
            )
        except stripe.error.AuthenticationError as e:
            logger.error(f"Stripe Authentication Error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Payment processor authentication failed"
            )
        except stripe.error.APIConnectionError as e:
            logger.error(f"Stripe Connection Error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Payment processor temporarily unavailable"
            )
        except Exception as e:
            logger.error(f"Unexpected Stripe error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Payment processing failed"
            )

    async def confirm_payment_intent(
        self,
        payment_intent_id: str,
        payment_method_id: str = None
    ) -> dict[str, Any]:
        """
        Confirm a Stripe Payment Intent
        
        Args:
            payment_intent_id: Stripe Payment Intent ID
            payment_method_id: Stripe Payment Method ID (optional if already attached)
        
        Returns:
            Dict containing confirmation result
        """
        try:
            confirm_params = {}
            if payment_method_id:
                confirm_params['payment_method'] = payment_method_id

            intent = stripe.PaymentIntent.confirm(
                payment_intent_id,
                **confirm_params
            )

            logger.info(f"Confirmed Stripe Payment Intent: {intent.id}, Status: {intent.status}")

            return {
                "payment_intent_id": intent.id,
                "status": intent.status,
                "amount_received": intent.amount_received / 100,  # Convert back to currency units
                "charges": [self._format_charge(charge) for charge in intent.charges.data] if intent.charges else []
            }

        except stripe.error.CardError as e:
            logger.error(f"Card Error during confirmation: {e.user_message}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment failed: {e.user_message}"
            )
        except Exception as e:
            logger.error(f"Error confirming payment intent: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Payment confirmation failed"
            )

    async def retrieve_payment_intent(self, payment_intent_id: str) -> dict[str, Any]:
        """
        Retrieve a Stripe Payment Intent
        
        Args:
            payment_intent_id: Stripe Payment Intent ID
        
        Returns:
            Dict containing payment intent details
        """
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            return {
                "payment_intent_id": intent.id,
                "status": intent.status,
                "amount": intent.amount / 100,
                "currency": intent.currency.upper(),
                "created": intent.created,
                "metadata": intent.metadata,
                "last_payment_error": intent.last_payment_error
            }

        except stripe.error.InvalidRequestError:
            logger.error(f"Invalid Payment Intent ID: {payment_intent_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )
        except Exception as e:
            logger.error(f"Error retrieving payment intent: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve payment information"
            )

    # ─── CUSTOMER OPERATIONS ──────────────────────────────────────────────
    async def create_customer(
        self,
        email: str,
        name: str = None,
        metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Create a Stripe Customer
        
        Args:
            email: Customer email
            name: Customer name
            metadata: Additional metadata
        
        Returns:
            Dict containing customer details
        """
        try:
            customer_data = {
                "email": email,
                "metadata": metadata or {}
            }
            if name:
                customer_data["name"] = name

            customer = stripe.Customer.create(**customer_data)

            logger.info(f"Created Stripe Customer: {customer.id} for email: {email}")

            return {
                "customer_id": customer.id,
                "email": customer.email,
                "name": customer.name,
                "created": customer.created
            }

        except Exception as e:
            logger.error(f"Error creating Stripe customer: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create customer profile"
            )

    async def retrieve_customer(self, customer_id: str) -> dict[str, Any]:
        """
        Retrieve a Stripe Customer
        
        Args:
            customer_id: Stripe Customer ID
        
        Returns:
            Dict containing customer details
        """
        try:
            customer = stripe.Customer.retrieve(customer_id)

            return {
                "customer_id": customer.id,
                "email": customer.email,
                "name": customer.name,
                "created": customer.created,
                "default_source": customer.default_source
            }

        except stripe.error.InvalidRequestError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        except Exception as e:
            logger.error(f"Error retrieving customer: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve customer"
            )

    # ─── REFUND OPERATIONS ────────────────────────────────────────────────
    async def create_refund(
        self,
        payment_intent_id: str,
        amount: Decimal | None = None,
        reason: str = "requested_by_customer",
        metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Create a refund for a Stripe payment
        
        Args:
            payment_intent_id: Original Payment Intent ID
            amount: Refund amount (if partial, otherwise full refund)
            reason: Refund reason
            metadata: Additional metadata
        
        Returns:
            Dict containing refund details
        """
        try:
            refund_data = {
                "payment_intent": payment_intent_id,
                "reason": reason,
                "metadata": metadata or {}
            }

            if amount:
                refund_data["amount"] = int(amount * 100)  # Convert to cents

            refund = stripe.Refund.create(**refund_data)

            logger.info(f"Created Stripe Refund: {refund.id} for Payment Intent: {payment_intent_id}")

            return {
                "refund_id": refund.id,
                "payment_intent_id": payment_intent_id,
                "amount": refund.amount / 100,
                "currency": refund.currency.upper(),
                "status": refund.status,
                "reason": refund.reason,
                "created": refund.created
            }

        except stripe.error.InvalidRequestError as e:
            logger.error(f"Invalid refund request: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Refund failed: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error creating refund: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Refund processing failed"
            )

    # ─── WEBHOOK PROCESSING ───────────────────────────────────────────────
    async def process_webhook(self, payload: bytes, signature: str) -> dict[str, Any]:
        """
        Process Stripe webhook events
        
        Args:
            payload: Raw webhook payload
            signature: Stripe signature header
        
        Returns:
            Dict containing processed event information
        """
        try:
            # Verify webhook signature
            event = stripe.Webhook.construct_event(
                payload, signature, settings.STRIPE_WEBHOOK_SECRET
            )

            logger.info(f"Processing Stripe webhook: {event['type']}")

            # Handle different event types
            event_type = event['type']
            event_data = event['data']['object']

            if event_type == 'payment_intent.succeeded':
                await self._handle_payment_succeeded(event_data)
            elif event_type == 'payment_intent.payment_failed':
                await self._handle_payment_failed(event_data)
            elif event_type == 'charge.dispute.created':
                await self._handle_chargeback_created(event_data)
            elif event_type == 'invoice.payment_succeeded':
                await self._handle_invoice_paid(event_data)

            return {
                "event_id": event['id'],
                "event_type": event_type,
                "processed": True
            }

        except ValueError as e:
            logger.error(f"Invalid webhook payload: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid payload"
            )
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid signature"
            )
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Webhook processing failed"
            )

    # ─── PRIVATE METHODS ──────────────────────────────────────────────────
    def _format_charge(self, charge) -> dict[str, Any]:
        """Format Stripe charge object for response"""
        return {
            "charge_id": charge.id,
            "amount": charge.amount / 100,
            "currency": charge.currency.upper(),
            "status": charge.status,
            "created": charge.created,
            "payment_method_details": charge.payment_method_details
        }

    async def _handle_payment_succeeded(self, payment_intent) -> None:
        """Handle successful payment webhook"""
        payment_id = payment_intent.get('metadata', {}).get('brain2gain_payment_id')

        if payment_id:
            # Update payment status in database
            try:
                payment = self.session.get(Payment, uuid.UUID(payment_id))
                if payment:
                    payment.status = PaymentStatus.CAPTURED
                    payment.captured_at = datetime.utcnow()
                    payment.stripe_payment_intent_id = payment_intent['id']
                    payment.gateway_response = payment_intent

                    self.session.add(payment)
                    self.session.commit()

                    logger.info(f"Updated payment {payment_id} status to CAPTURED")
            except Exception as e:
                logger.error(f"Failed to update payment status: {str(e)}")

    async def _handle_payment_failed(self, payment_intent) -> None:
        """Handle failed payment webhook"""
        payment_id = payment_intent.get('metadata', {}).get('brain2gain_payment_id')

        if payment_id:
            try:
                payment = self.session.get(Payment, uuid.UUID(payment_id))
                if payment:
                    payment.status = PaymentStatus.FAILED
                    payment.failed_at = datetime.utcnow()
                    payment.failure_reason = payment_intent.get('last_payment_error', {}).get('message', 'Payment failed')
                    payment.gateway_response = payment_intent

                    self.session.add(payment)
                    self.session.commit()

                    logger.info(f"Updated payment {payment_id} status to FAILED")
            except Exception as e:
                logger.error(f"Failed to update payment status: {str(e)}")

    async def _handle_chargeback_created(self, dispute) -> None:
        """Handle chargeback/dispute webhook"""
        logger.warning(f"Chargeback created for charge: {dispute.get('charge')}")
        # TODO: Implement chargeback handling logic

    async def _handle_invoice_paid(self, invoice) -> None:
        """Handle subscription invoice payment webhook"""
        logger.info(f"Invoice paid: {invoice.get('id')}")
        # TODO: Implement subscription handling if needed
