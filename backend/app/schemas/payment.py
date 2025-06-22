# backend/app/schemas/payment.py
import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models import PaymentStatus


# ─── PAYMENT SCHEMAS ──────────────────────────────────────────────────
class PaymentBase(BaseModel):
    amount: Decimal = Field(..., ge=0, description="Payment amount")
    currency: str = Field("MXN", min_length=3, max_length=3, description="Currency code")
    payment_method: str = Field(..., description="Payment method: stripe, paypal, bank_transfer")

class PaymentCreate(PaymentBase):
    """Schema for creating a payment"""
    order_id: uuid.UUID = Field(..., description="Order ID this payment belongs to")

class PaymentProcess(BaseModel):
    """Schema for processing payment with gateway"""
    payment_id: uuid.UUID
    payment_method_data: dict = Field(..., description="Payment method specific data")

    # Stripe specific fields
    stripe_payment_method_id: str | None = None
    stripe_customer_id: str | None = None

    # PayPal specific fields
    paypal_order_id: str | None = None

class PaymentRead(PaymentBase):
    payment_id: uuid.UUID
    order_id: uuid.UUID
    status: PaymentStatus

    # Gateway references
    stripe_payment_intent_id: str | None
    paypal_order_id: str | None
    gateway_transaction_id: str | None

    # Processing details
    gateway_response: str | None  # JSON string
    failure_reason: str | None

    # Timestamps
    created_at: datetime
    authorized_at: datetime | None
    captured_at: datetime | None
    failed_at: datetime | None

    model_config = {"from_attributes": True}

class PaymentSummary(BaseModel):
    """Simplified payment info for lists"""
    payment_id: uuid.UUID
    order_id: uuid.UUID
    amount: Decimal
    currency: str
    payment_method: str
    status: PaymentStatus
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── REFUND SCHEMAS ───────────────────────────────────────────────────
class RefundBase(BaseModel):
    amount: Decimal = Field(..., ge=0, description="Refund amount")
    reason: str = Field(..., min_length=1, max_length=500, description="Refund reason")

class RefundCreate(RefundBase):
    """Schema for creating a refund"""
    payment_id: uuid.UUID = Field(..., description="Payment ID to refund")

class RefundRead(RefundBase):
    refund_id: uuid.UUID
    payment_id: uuid.UUID
    order_id: uuid.UUID
    status: str
    gateway_refund_id: str | None
    created_at: datetime
    processed_at: datetime | None

    model_config = {"from_attributes": True}


# ─── PAYMENT GATEWAY RESPONSES ────────────────────────────────────────
class StripePaymentResponse(BaseModel):
    """Response from Stripe payment processing"""
    success: bool
    payment_intent_id: str | None = None
    client_secret: str | None = None
    status: str
    error_message: str | None = None
    requires_action: bool = False
    redirect_url: str | None = None

class PayPalPaymentResponse(BaseModel):
    """Response from PayPal payment processing"""
    success: bool
    order_id: str | None = None
    approval_url: str | None = None
    status: str
    error_message: str | None = None

class BankTransferResponse(BaseModel):
    """Response for bank transfer payment method"""
    success: bool
    reference_number: str
    bank_details: dict
    instructions: str
    expiry_date: datetime


# ─── PAYMENT PROCESSING RESPONSES ─────────────────────────────────────
class PaymentProcessResponse(BaseModel):
    """Generic payment processing response"""
    success: bool
    payment_id: uuid.UUID
    status: PaymentStatus
    message: str

    # Gateway specific responses
    stripe_response: StripePaymentResponse | None = None
    paypal_response: PayPalPaymentResponse | None = None
    bank_transfer_response: BankTransferResponse | None = None

    # Additional actions required
    requires_user_action: bool = False
    action_url: str | None = None
    next_step: str | None = None


# ─── WEBHOOK SCHEMAS ──────────────────────────────────────────────────
class StripeWebhookEvent(BaseModel):
    """Schema for Stripe webhook events"""
    event_id: str
    event_type: str
    payment_intent_id: str
    status: str
    amount: Decimal
    currency: str
    metadata: dict = {}

class PayPalWebhookEvent(BaseModel):
    """Schema for PayPal webhook events"""
    event_id: str
    event_type: str
    order_id: str
    status: str
    amount: Decimal
    currency: str


# ─── PAYMENT STATISTICS ───────────────────────────────────────────────
class PaymentStats(BaseModel):
    """Payment statistics for admin dashboard"""
    total_payments: int
    successful_payments: int
    failed_payments: int
    pending_payments: int

    total_amount: Decimal
    total_refunds: Decimal
    net_revenue: Decimal

    stripe_payments: int
    paypal_payments: int
    bank_transfer_payments: int

    average_payment_amount: Decimal
    conversion_rate: float  # successful payments / total attempts


# ─── PAYMENT FILTERS ──────────────────────────────────────────────────
class PaymentFilters(BaseModel):
    """Filters for payment listing"""
    status: list[PaymentStatus] | None = None
    payment_method: list[str] | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    min_amount: Decimal | None = None
    max_amount: Decimal | None = None
    order_id: uuid.UUID | None = None


# ─── PAYMENT METHODS CONFIGURATION ────────────────────────────────────
class PaymentMethodConfig(BaseModel):
    """Configuration for available payment methods"""
    method: str
    enabled: bool
    display_name: str
    description: str
    icon_url: str | None = None
    min_amount: Decimal | None = None
    max_amount: Decimal | None = None
    currencies: list[str] = ["MXN"]
    processing_fee_percentage: Decimal = Field(0, ge=0, le=100)
    fixed_fee: Decimal = Field(0, ge=0)

class PaymentMethodsList(BaseModel):
    """List of available payment methods"""
    methods: list[PaymentMethodConfig]
    default_method: str
    currency: str = "MXN"
