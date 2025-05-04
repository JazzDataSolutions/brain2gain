# backend/app/schemas/transaction.py
from pydantic import BaseModel
from datetime import date
from decimal import Decimal
from app.models.transaction import TransactionType

class TransactionBase(BaseModel):
    type: TransactionType
    amount: Decimal
    description: str | None
    customer_id: int | None
    product_id: int | None

class TransactionCreate(TransactionBase):
    due_date: date | None

class TransactionRead(TransactionBase):
    tx_id: int
    paid: bool
    due_date: date | None
    paid_date: date | None

    model_config = {"from_attributes": True}

