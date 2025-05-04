# backend/app/schemas/stock.py
from pydantic import BaseModel

class StockRead(BaseModel):
    product_id: int
    quantity: int

    model_config = {"from_attributes": True}

