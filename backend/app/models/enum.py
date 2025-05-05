# backend/app/models/enums.py
from __future__ import annotations
import enum
from sqlalchemy import Enum


class ProductStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    DISCONTINUED = "DISCONTINUED"

class OrderStatus(str, enum.Enum):
    PENDING   = "PENDING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

