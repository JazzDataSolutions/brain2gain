# backend/app/models/product.py
from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING
from decimal import Decimal
from datetime import datetime
from enum import Enum

from sqlmodel import SQLModel, Field, Column, Relationship
from sqlalchemy import CheckConstraint, Enum as SQLEnum

class ProductStatus(str, Enum):
    ACTIVE        = "ACTIVE"
    DISCONTINUED  = "DISCONTINUED"


class Product(SQLModel, table=True):
    product_id:   Optional[int]     = Field(default=None, primary_key=True)
    sku:          str               = Field(index=True, nullable=False, unique=True)
    name:         str               = Field(nullable=False)
    unit_price:   Decimal           = Field(
        sa_column=Column(
            "unit_price",
            CheckConstraint("unit_price >= 0", name="ck_product_unit_price_non_negative"),
            nullable=False
        )
    )
    status:       ProductStatus     = Field(
        sa_column=Column(SQLEnum(ProductStatus)),
        default=ProductStatus.ACTIVE,
        nullable=False
    )
    created_at:   datetime          = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at:   datetime          = Field(default_factory=datetime.utcnow, nullable=False)
    
    stock: Optional["Stock"] = Relationship(back_populates="product")
    sales_items:  List["SalesItem"] = Relationship(back_populates="product")
