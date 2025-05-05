# backend/app/models/stock.py
from __future__ import annotations

from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

class Stock(SQLModel, table=True):
    stock_id:    Optional[int]      = Field(default=None, primary_key=True)
    product_id:  int                = Field(foreign_key="product.product_id", nullable=False)
    quantity:    int                = Field(ge=0, nullable=False)
    updated_at:  datetime           = Field(default_factory=datetime.utcnow, nullable=False)

    # Forward‐ref con string. No hay import de Product aquí.
    product:     "Product"          = Relationship(back_populates="stock")

