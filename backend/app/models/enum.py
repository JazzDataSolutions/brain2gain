# backend/app/models/enums.py
import enum
from sqlalchemy import Enum

class ProductStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    DISCONTINUED = "DISCONTINUED"

class OrderStatus(str, enum.Enum):
    PENDING   = "PENDING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

