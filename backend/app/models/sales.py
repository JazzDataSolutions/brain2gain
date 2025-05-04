# backend/app/models/sales.py
from typing import List, Optional
from datetime import datetime
from decimal import Decimal                
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import CheckConstraint, Column, Enum as SQLEnum, DateTime
from .transaction import TransactionType

class OrderStatus(str, Enum):
    PENDING    = "PENDING"
    COMPLETED  = "COMPLETED"
    CANCELLED  = "CANCELLED"

class SalesOrder(SQLModel, table=True):
    so_id:        Optional[int]      = Field(default=None, primary_key=True)
    customer_id:  int                = Field(foreign_key="customer.customer_id", nullable=False)
    order_date:   datetime           = Field(default_factory=datetime.utcnow, nullable=False)
    status:       OrderStatus        = Field(sa_column=Column(SQLEnum(OrderStatus)), default=OrderStatus.PENDING, nullable=False)
    created_at:   datetime           = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at:   datetime           = Field(default_factory=datetime.utcnow, nullable=False)

    customer:     "Customer"         = Relationship(back_populates="orders")
    items:        List["SalesItem"]  = Relationship(back_populates="order")

class SalesItem(SQLModel, table=True):
    so_id:        int                = Field(foreign_key="salesorder.so_id", primary_key=True)
    product_id:   int                = Field(foreign_key="product.product_id", primary_key=True)
    qty:          int                = Field(nullable=False, gt=0)
    unit_price:   Decimal            = Field(nullable=False, ge=0)
    created_at:   datetime           = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at:   datetime           = Field(default_factory=datetime.utcnow, nullable=False)

    order:        SalesOrder         = Relationship(back_populates="items")
    product:      "Product"          = Relationship(back_populates="sales_items")

