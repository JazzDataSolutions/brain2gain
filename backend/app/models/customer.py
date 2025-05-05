# backend/app/models/customer.py
from __future__ import annotations

from typing import List, Optional 
from datetime import datetime 
from pydantic import EmailStr 
from sqlmodel import SQLModel, Field, Relationship

class Customer(SQLModel, table=True):
    customer_id:  Optional[int]     = Field(default=None, primary_key=True)
    first_name:   str               = Field(nullable=False)
    last_name:    str               = Field(nullable=False)
    email:        EmailStr          = Field(index=True, unique=True, nullable=False)
    phone:        Optional[str]     = None
    created_at:   datetime          = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at:   datetime          = Field(default_factory=datetime.utcnow, nullable=False)

    orders:       List["SalesOrder"] = Relationship(back_populates="customer")
    transactions: list["Transaction"] = Relationship(back_populates="customer")
