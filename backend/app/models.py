# backend/app/models.py
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import EmailStr
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy.orm import configure_mappers

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
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class TransactionType(str, Enum):
    SALE     = "SALE"
    PURCHASE = "PURCHASE"
    CREDIT   = "CREDIT"
    PAYMENT  = "PAYMENT"

# ─── USERS ────────────────────────────────────────────────────────────────
class UserRoleLink(SQLModel, table=True):
    user_id: Optional[int] = Field(default=None, foreign_key="user.user_id", primary_key=True)
    role_id: Optional[int] = Field(default=None, foreign_key="role.role_id", primary_key=True)

class User(SQLModel, table=True):
    user_id: Optional[int] = Field(default=None, primary_key=True)
    username: str        = Field(unique=True, index=True, nullable=False)
    email:    EmailStr   = Field(unique=True, index=True, nullable=False)
    hashed_password: str = Field(nullable=False)
    is_active: bool      = Field(default=True, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    roles: List["Role"] = Relationship(back_populates="users", link_model=UserRoleLink)

class Role(SQLModel, table=True):
    role_id: Optional[int] = Field(default=None, primary_key=True)
    name: UserRoleEnum = Field(unique=True, nullable=False)

    users: List[User] = Relationship(back_populates="roles", link_model=UserRoleLink)

# ─── PRODUCT & INVENTORY ──────────────────────────────────────────────────
class Product(SQLModel, table=True):
    product_id: Optional[int] = Field(default=None, primary_key=True)
    sku:        str           = Field(unique=True, index=True, nullable=False)
    name:       str           = Field(nullable=False)
    unit_price: Decimal       = Field(ge=0, nullable=False)
    status:     ProductStatus = Field(default=ProductStatus.ACTIVE, nullable=False)
    created_at: datetime      = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime      = Field(default_factory=datetime.utcnow, nullable=False)

    stock: "Stock" = Relationship(back_populates="product", sa_relationship_kwargs={"uselist": False})
    sales_items: List["SalesItem"] = Relationship(back_populates="product")
    transactions: List["Transaction"] = Relationship(back_populates="product")

class Stock(SQLModel, table=True):
    stock_id:   Optional[int] = Field(default=None, primary_key=True)
    product_id: int           = Field(foreign_key="product.product_id", unique=True, nullable=False)
    quantity:   int           = Field(ge=0, nullable=False)
    updated_at: datetime      = Field(default_factory=datetime.utcnow, nullable=False)

    product: "Product" = Relationship(back_populates="stock")

# ─── SALES ────────────────────────────────────────────────────────────────
class Customer(SQLModel, table=True):
    customer_id: Optional[int] = Field(default=None, primary_key=True)
    first_name:  str           = Field(nullable=False)
    last_name:   str           = Field(nullable=False)
    email:       EmailStr      = Field(unique=True, index=True, nullable=False)
    phone:       Optional[str] = None
    created_at:  datetime      = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at:  datetime      = Field(default_factory=datetime.utcnow, nullable=False)

    orders:       List["SalesOrder"] = Relationship(back_populates="customer")
    transactions: List["Transaction"] = Relationship(back_populates="customer")

class SalesOrder(SQLModel, table=True):
    so_id:       Optional[int] = Field(default=None, primary_key=True)
    customer_id: int           = Field(foreign_key="customer.customer_id", nullable=False)
    order_date:  datetime      = Field(default_factory=datetime.utcnow, nullable=False)
    status:      OrderStatus   = Field(default=OrderStatus.PENDING, nullable=False)
    created_at:  datetime      = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at:  datetime      = Field(default_factory=datetime.utcnow, nullable=False)

    customer: "Customer"          = Relationship(back_populates="orders")
    items:    List["SalesItem"]   = Relationship(back_populates="order")

class SalesItem(SQLModel, table=True):
    so_id:      int      = Field(foreign_key="salesorder.so_id", primary_key=True)
    product_id: int      = Field(foreign_key="product.product_id", primary_key=True)
    qty:        int      = Field(gt=0, nullable=False)
    unit_price: Decimal  = Field(ge=0, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    order:   "SalesOrder" = Relationship(back_populates="items")
    product: "Product"    = Relationship(back_populates="sales_items")

# ─── TRANSACTIONS ─────────────────────────────────────────────────────────
class Transaction(SQLModel, table=True):
    tx_id:       Optional[int]     = Field(default=None, primary_key=True)
    tx_type:     TransactionType   = Field(nullable=False)
    amount:      Decimal           = Field(ge=0, nullable=False)
    description: Optional[str]     = None
    customer_id: Optional[int]     = Field(default=None, foreign_key="customer.customer_id")
    product_id:  Optional[int]     = Field(default=None, foreign_key="product.product_id")
    due_date:    Optional[date]    = None
    paid:        bool              = Field(default=False)
    paid_date:   Optional[date]    = None
    created_at:  datetime          = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at:  datetime          = Field(default_factory=datetime.utcnow, nullable=False)

    customer: Optional["Customer"] = Relationship(back_populates="transactions")
    product:  Optional["Product"]  = Relationship(back_populates="transactions")

# ─── Ensure all mappers configure after declarations ─────────────────────
configure_mappers()

