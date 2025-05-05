from pydantic import BaseModel
from decimal import Decimal

class ProductBase(BaseModel):
    sku: str
    name: str
    unit_price: Decimal

    class Config:
        orm_mode = True

class ProductCreate(ProductBase):
    pass

class ProductRead(ProductBase):
    product_id: int

    model_config = {"from_attributes": True}

