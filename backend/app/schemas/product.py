# backend/app/schemas/product.py
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

# Reutiliza tu Enum de modelo o redefine si prefieres
class ProductStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DISCONTINUED = "DISCONTINUED"

class ProductBase(BaseModel):
    sku: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=255)
    unit_price: Decimal = Field(..., ge=0)
    status: Optional[ProductStatus] = Field(default=ProductStatus.ACTIVE)

class ProductCreate(ProductBase):
    pass

class ProductRead(ProductBase):
    product_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

