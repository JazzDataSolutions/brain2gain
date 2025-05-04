# backend/app/models/stock.py
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

class Stock(SQLModel, table=True):
    product_id:   int               = Field(foreign_key="product.product_id", primary_key=True)
    quantity:     int               = Field(default=0)
    updated_at:   datetime          = Field(default_factory=datetime.utcnow, nullable=False)

    # Relationship con string en lugar de clase directa
    product:      "Product"         = Relationship(back_populates="stock")

