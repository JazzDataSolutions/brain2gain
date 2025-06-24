# backend/app/models.py
import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

import sqlalchemy as sa
from pydantic import EmailStr
from sqlalchemy.orm import configure_mappers
from sqlmodel import Field, Relationship, SQLModel


# ─── ENUMS ────────────────────────────────────────────────────────────────
class UserRoleEnum(str, Enum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    SELLER = "SELLER"
    ACCOUNTANT = "ACCOUNTANT"


class ProductStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DISCONTINUED = "DISCONTINUED"


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    PROCESSING = "PROCESSING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"


class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    AUTHORIZED = "AUTHORIZED"
    CAPTURED = "CAPTURED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"
    CANCELLED = "CANCELLED"


class TransactionType(str, Enum):
    SALE = "SALE"
    PURCHASE = "PURCHASE"
    CREDIT = "CREDIT"
    PAYMENT = "PAYMENT"


# ─── USERS ────────────────────────────────────────────────────────────────
# Shared properties


class UserRoleLink(SQLModel, table=True):
    user_id: uuid.UUID | None = Field(
        default=None, foreign_key="user.id", primary_key=True
    )
    role_id: int | None = Field(
        default=None, foreign_key="role.role_id", primary_key=True
    )


class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)


class UserRegister(SQLModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=40)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=40)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    items: list["Item"] = Relationship(back_populates="owner")
    orders: list["Order"] = Relationship(back_populates="user")
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    roles: list["Role"] = Relationship(back_populates="users", link_model=UserRoleLink)


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


class Role(SQLModel, table=True):
    role_id: int | None = Field(default=None, primary_key=True)
    name: UserRoleEnum = Field(unique=True, nullable=False)
    users: list[User] = Relationship(back_populates="roles", link_model=UserRoleLink)


# ─── ITEMS ────────────────────────────────────────────────────────────────


# Shared properties
class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on item creation
class ItemCreate(ItemBase):
    pass


# Properties to receive on item update
class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


# Database model, database table inferred from class name
class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str = Field(max_length=255)
    owner_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    owner: User | None = Relationship(back_populates="items")


# Properties to return via API, id is always required
class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int


# ─── TOKENS ────────────────────────────────────────────────────────────────


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=40)


# ─── PRODUCT & INVENTORY ──────────────────────────────────────────────────


class Product(SQLModel, table=True):
    product_id: int | None = Field(default=None, primary_key=True)
    sku: str = Field(unique=True, index=True, nullable=False)
    name: str = Field(nullable=False)
    description: str | None = Field(default=None)
    unit_price: Decimal = Field(ge=0, nullable=False)
    category: str | None = Field(default=None)
    brand: str | None = Field(default=None)
    status: ProductStatus = Field(default=ProductStatus.ACTIVE, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    stock: "Stock" = Relationship(
        back_populates="product", sa_relationship_kwargs={"uselist": False}
    )
    sales_items: list["SalesItem"] = Relationship(back_populates="product")
    order_items: list["OrderItem"] = Relationship(back_populates="product")
    transactions: list["Transaction"] = Relationship(back_populates="product")


class Stock(SQLModel, table=True):
    stock_id: int | None = Field(default=None, primary_key=True)
    product_id: int = Field(
        foreign_key="product.product_id", unique=True, nullable=False
    )
    quantity: int = Field(ge=0, nullable=False)
    min_stock_level: int = Field(ge=0, nullable=False, default=0)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    product: "Product" = Relationship(back_populates="stock")


# ─── SALES ────────────────────────────────────────────────────────────────


class Customer(SQLModel, table=True):
    customer_id: int | None = Field(default=None, primary_key=True)
    first_name: str = Field(nullable=False)
    last_name: str = Field(nullable=False)
    email: EmailStr = Field(unique=True, index=True, nullable=False)
    phone: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    orders: list["SalesOrder"] = Relationship(back_populates="customer")
    transactions: list["Transaction"] = Relationship(back_populates="customer")


# ─── ORDERS (New microservices-compatible models) ──────────────────────
class Order(SQLModel, table=True):
    __tablename__ = "orders"

    order_id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    status: OrderStatus = Field(default=OrderStatus.PENDING, nullable=False)

    # Financial details
    subtotal: Decimal = Field(ge=0, nullable=False)
    tax_amount: Decimal = Field(ge=0, nullable=False, default=0)
    shipping_cost: Decimal = Field(ge=0, nullable=False, default=0)
    total_amount: Decimal = Field(ge=0, nullable=False)

    # Payment details
    payment_method: str | None = Field(default=None, max_length=50)
    payment_status: PaymentStatus = Field(default=PaymentStatus.PENDING, nullable=False)

    # Shipping details (JSON fields for flexibility)
    shipping_address: str | None = Field(default=None, sa_column=sa.Column(sa.JSON))
    billing_address: str | None = Field(default=None, sa_column=sa.Column(sa.JSON))

    # Additional details
    notes: str | None = Field(default=None)
    tracking_number: str | None = Field(default=None, max_length=100)
    estimated_delivery: datetime | None = Field(default=None)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    completed_at: datetime | None = Field(default=None)
    cancelled_at: datetime | None = Field(default=None)

    # Migration tracking
    migrated_from_sales_order_id: uuid.UUID | None = Field(default=None)

    # Relationships
    user: "User" = Relationship(back_populates="orders")
    items: list["OrderItem"] = Relationship(back_populates="order")
    payments: list["Payment"] = Relationship(back_populates="order")
    refunds: list["Refund"] = Relationship(back_populates="order")


class OrderItem(SQLModel, table=True):
    __tablename__ = "order_items"

    item_id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    order_id: uuid.UUID = Field(foreign_key="orders.order_id", nullable=False)
    product_id: int = Field(foreign_key="product.product_id", nullable=False)

    # Denormalized fields for historical record keeping
    product_name: str = Field(max_length=200, nullable=False)
    product_sku: str = Field(max_length=100, nullable=False)

    # Quantity and pricing
    quantity: int = Field(gt=0, nullable=False)
    unit_price: Decimal = Field(ge=0, nullable=False)
    line_total: Decimal = Field(ge=0, nullable=False)
    discount_amount: Decimal = Field(ge=0, nullable=False, default=0)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # Migration tracking
    migrated_from_sales_item_id: uuid.UUID | None = Field(default=None)

    # Relationships
    order: "Order" = Relationship(back_populates="items")
    product: "Product" = Relationship(back_populates="order_items")


# ─── PAYMENT MODELS ──────────────────────────────────────────────────
class Payment(SQLModel, table=True):
    __tablename__ = "payments"

    payment_id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    order_id: uuid.UUID = Field(foreign_key="orders.order_id", nullable=False)

    # Payment details
    amount: Decimal = Field(ge=0, nullable=False)
    currency: str = Field(default="MXN", max_length=3, nullable=False)
    payment_method: str = Field(
        max_length=50, nullable=False
    )  # stripe, paypal, bank_transfer

    # Status and processing
    status: PaymentStatus = Field(default=PaymentStatus.PENDING, nullable=False)

    # External references (gateway transaction IDs)
    stripe_payment_intent_id: str | None = Field(default=None, max_length=255)
    paypal_order_id: str | None = Field(default=None, max_length=255)
    gateway_transaction_id: str | None = Field(default=None, max_length=255)

    # Payment processing details
    gateway_response: str | None = Field(default=None, sa_column=sa.Column(sa.JSON))
    failure_reason: str | None = Field(default=None, max_length=500)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    authorized_at: datetime | None = Field(default=None)
    captured_at: datetime | None = Field(default=None)
    failed_at: datetime | None = Field(default=None)

    # Relationships
    order: "Order" = Relationship(back_populates="payments")
    refunds: list["Refund"] = Relationship(back_populates="payment")


class Refund(SQLModel, table=True):
    __tablename__ = "refunds"

    refund_id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    payment_id: uuid.UUID = Field(foreign_key="payments.payment_id", nullable=False)
    order_id: uuid.UUID = Field(foreign_key="orders.order_id", nullable=False)

    # Refund details
    amount: Decimal = Field(ge=0, nullable=False)
    reason: str = Field(max_length=500, nullable=False)

    # Processing details
    gateway_refund_id: str | None = Field(default=None, max_length=255)
    status: str = Field(
        default="PENDING", max_length=20, nullable=False
    )  # PENDING, COMPLETED, FAILED

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    processed_at: datetime | None = Field(default=None)

    # Relationships
    payment: "Payment" = Relationship(back_populates="refunds")
    order: "Order" = Relationship(back_populates="refunds")


# ─── LEGACY SALES MODELS (Keep for backward compatibility) ───────────
class SalesOrder(SQLModel, table=True):
    so_id: int | None = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customer.customer_id", nullable=False)
    order_date: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    status: OrderStatus = Field(default=OrderStatus.PENDING, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    customer: "Customer" = Relationship(back_populates="orders")
    items: list["SalesItem"] = Relationship(back_populates="order")


class SalesItem(SQLModel, table=True):
    so_id: int = Field(foreign_key="salesorder.so_id", primary_key=True)
    product_id: int = Field(foreign_key="product.product_id", primary_key=True)
    qty: int = Field(gt=0, nullable=False)
    unit_price: Decimal = Field(ge=0, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    order: "SalesOrder" = Relationship(back_populates="items")
    product: "Product" = Relationship(back_populates="sales_items")


# ─── SHOPPING CART ────────────────────────────────────────────────────────


class Cart(SQLModel, table=True):
    cart_id: int | None = Field(default=None, primary_key=True)
    user_id: uuid.UUID | None = Field(default=None, foreign_key="user.id")
    session_id: str | None = Field(default=None, index=True)  # For guest carts
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    items: list["CartItem"] = Relationship(back_populates="cart")
    user: Optional["User"] = Relationship()


class CartItem(SQLModel, table=True):
    cart_id: int = Field(foreign_key="cart.cart_id", primary_key=True)
    product_id: int = Field(foreign_key="product.product_id", primary_key=True)
    quantity: int = Field(ge=1, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    cart: "Cart" = Relationship(back_populates="items")
    product: "Product" = Relationship()


# ─── TRANSACTIONS ─────────────────────────────────────────────────────────
class Transaction(SQLModel, table=True):
    tx_id: int | None = Field(default=None, primary_key=True)
    tx_type: TransactionType = Field(nullable=False)
    amount: Decimal = Field(ge=0, nullable=False)
    description: str | None = None
    customer_id: int | None = Field(default=None, foreign_key="customer.customer_id")
    product_id: int | None = Field(default=None, foreign_key="product.product_id")
    due_date: date | None = None
    paid: bool = Field(default=False)
    paid_date: date | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    customer: Optional["Customer"] = Relationship(back_populates="transactions")
    product: Optional["Product"] = Relationship(back_populates="transactions")


# ─── Ensure all mappers configure after declarations ─────────────────────
configure_mappers()
