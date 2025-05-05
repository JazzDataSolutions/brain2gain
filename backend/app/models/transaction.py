# backend/app/models/transaction.py
from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from datetime import date, datetime
from enum import Enum
from decimal import Decimal
from sqlmodel import SQLModel, Field, Relationship


# Importa explícitamente las entidades relacionadas
if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.product  import Product

# Importamos Customer y Product como cadenas para evitar orden de carga
class TransactionType(str, Enum):
    SALE     = "SALE"
    PURCHASE = "PURCHASE"
    CREDIT   = "CREDIT"
    PAYMENT  = "PAYMENT"

class Transaction(SQLModel, table=True):
    __tablename__  = "transaction"
    __table_args__ = {"extend_existing": True}

    tx_id:        Optional[int]   = Field(default=None, primary_key=True)
    type:         TransactionType = Field(nullable=False)
    amount:       Decimal         = Field(nullable=False, ge=0)
    description:  Optional[str]   = Field(default=None)
    customer_id:  Optional[int]   = Field(default=None, foreign_key="customer.customer_id")
    product_id:   Optional[int]   = Field(default=None, foreign_key="product.product_id")
    due_date:     Optional[date]  = Field(default=None)
    paid:         bool            = Field(default=False)
    paid_date:    Optional[date]  = Field(default=None)
    created_at:   datetime        = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at:   datetime        = Field(default_factory=datetime.utcnow, nullable=False)

    # Usamos strings en Relationship para referencias adelantadas
    customer:     Optional["Customer"] = Relationship(back_populates="transactions")
    product:      "Product"            = Relationship(back_populates="stock")


