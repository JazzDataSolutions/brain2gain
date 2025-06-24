# backend/app/schemas/order.py
import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models import OrderStatus, PaymentStatus


# ─── ORDER ITEM SCHEMAS ──────────────────────────────────────────────
class OrderItemBase(BaseModel):
    product_id: int = Field(..., gt=0, description="Product ID")
    quantity: int = Field(..., gt=0, description="Quantity ordered")
    unit_price: Decimal = Field(..., ge=0, description="Unit price at time of order")
    discount_amount: Decimal = Field(0, ge=0, description="Discount applied")


class OrderItemCreate(OrderItemBase):
    pass


class OrderItemRead(OrderItemBase):
    item_id: uuid.UUID
    order_id: uuid.UUID
    product_name: str
    product_sku: str
    line_total: Decimal
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── ADDRESS SCHEMAS ──────────────────────────────────────────────────
class AddressSchema(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    company: str | None = Field(None, max_length=100)
    address_line_1: str = Field(..., min_length=1, max_length=200)
    address_line_2: str | None = Field(None, max_length=200)
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=1, max_length=100)
    postal_code: str = Field(..., min_length=1, max_length=20)
    country: str = Field(
        ..., min_length=2, max_length=2, description="ISO 2-letter country code"
    )
    phone: str | None = Field(None, max_length=20)


# ─── ORDER SCHEMAS ────────────────────────────────────────────────────
class OrderBase(BaseModel):
    notes: str | None = Field(None, max_length=1000, description="Order notes")


class OrderCreate(OrderBase):
    """Schema for creating an order from cart"""

    payment_method: str = Field(
        ..., description="Payment method: stripe, paypal, bank_transfer"
    )
    shipping_address: AddressSchema = Field(..., description="Shipping address")
    billing_address: AddressSchema | None = Field(
        None, description="Billing address (optional, defaults to shipping)"
    )


class OrderUpdate(BaseModel):
    """Schema for updating order status (admin only)"""

    status: OrderStatus | None = None
    payment_status: PaymentStatus | None = None
    tracking_number: str | None = Field(None, max_length=100)
    estimated_delivery: datetime | None = None
    notes: str | None = Field(None, max_length=1000)


class OrderRead(OrderBase):
    order_id: uuid.UUID
    user_id: uuid.UUID
    status: OrderStatus
    payment_status: PaymentStatus

    # Financial details
    subtotal: Decimal
    tax_amount: Decimal
    shipping_cost: Decimal
    total_amount: Decimal

    # Payment details
    payment_method: str | None

    # Shipping details
    shipping_address: dict | None
    billing_address: dict | None
    tracking_number: str | None
    estimated_delivery: datetime | None

    # Timestamps
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
    cancelled_at: datetime | None

    # Related data
    items: list[OrderItemRead] = []

    model_config = {"from_attributes": True}


class OrderSummary(BaseModel):
    """Simplified order info for lists"""

    order_id: uuid.UUID
    status: OrderStatus
    payment_status: PaymentStatus
    total_amount: Decimal
    created_at: datetime
    items_count: int

    model_config = {"from_attributes": True}


class OrderList(BaseModel):
    """Paginated order list response"""

    orders: list[OrderSummary]
    total: int
    page: int
    page_size: int
    total_pages: int


# ─── CHECKOUT SCHEMAS ─────────────────────────────────────────────────
class CheckoutInitiate(BaseModel):
    """Schema for initiating checkout process"""

    payment_method: str = Field(
        ..., description="Payment method: stripe, paypal, bank_transfer"
    )
    shipping_address: AddressSchema
    billing_address: AddressSchema | None = None


class CheckoutCalculation(BaseModel):
    """Schema for checkout cost calculation"""

    subtotal: Decimal
    tax_amount: Decimal
    shipping_cost: Decimal
    total_amount: Decimal
    items: list[OrderItemRead]


class CheckoutConfirmation(BaseModel):
    """Schema for final checkout confirmation"""

    order_id: uuid.UUID
    payment_required: bool
    payment_intent_id: str | None = None  # For Stripe
    payment_url: str | None = None  # For PayPal
    redirect_url: str | None = None


class CheckoutValidation(BaseModel):
    """Schema for checkout validation response"""

    valid: bool
    errors: list[str] = []
    warnings: list[str] = []
    calculation: CheckoutCalculation | None = None


# ─── ORDER STATISTICS ─────────────────────────────────────────────────
class OrderStats(BaseModel):
    """Order statistics for admin dashboard"""

    total_orders: int
    pending_orders: int
    processing_orders: int
    shipped_orders: int
    delivered_orders: int
    cancelled_orders: int

    total_revenue: Decimal
    average_order_value: Decimal

    orders_today: int
    orders_this_week: int
    orders_this_month: int


# ─── ORDER FILTERS ────────────────────────────────────────────────────
class OrderFilters(BaseModel):
    """Filters for order listing"""

    status: list[OrderStatus] | None = None
    payment_status: list[PaymentStatus] | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    min_amount: Decimal | None = None
    max_amount: Decimal | None = None
    search: str | None = Field(
        None, description="Search in order ID, customer name, or product names"
    )
