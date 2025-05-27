# backend/app/models.py
import uuid

from typing import List, Optional
from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import List, Optional
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
# Shared properties

class UserRoleLink(SQLModel, table=True):
    user_id: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id", primary_key=True)
    role_id: Optional[int] = Field(default=None, foreign_key="role.role_id", primary_key=True)

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
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    roles: List["Role"] = Relationship(back_populates="users", link_model=UserRoleLink)
    
# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID

class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int

class Role(SQLModel, table=True):
    role_id: Optional[int] = Field(default=None, primary_key=True)
    name: UserRoleEnum = Field(unique=True, nullable=False)
    users: List[User] = Relationship(back_populates="roles", link_model=UserRoleLink)
        
        
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
    

# ─── SHOPPING CART ────────────────────────────────────────────────────────

class Cart(SQLModel, table=True):
    cart_id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")
    session_id: Optional[str] = Field(default=None, index=True)  # For guest carts
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    items: List["CartItem"] = Relationship(back_populates="cart")
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
