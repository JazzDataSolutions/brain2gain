from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CartItemBase(BaseModel):
    product_id: int
    quantity: int = Field(ge=1)


class CartItemCreate(CartItemBase):
    pass


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1)


class CartItemRead(CartItemBase):
    product_name: str
    product_sku: str
    unit_price: Decimal
    total_price: Decimal

    model_config = ConfigDict(from_attributes=True)


class CartBase(BaseModel):
    user_id: UUID | None = None
    session_id: str | None = None


class CartCreate(CartBase):
    pass


class CartRead(CartBase):
    cart_id: int
    items: list[CartItemRead] = []
    total_amount: Decimal
    item_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AddToCartRequest(BaseModel):
    product_id: int
    quantity: int = Field(ge=1, default=1)


class UpdateCartItemRequest(BaseModel):
    quantity: int = Field(ge=1)
