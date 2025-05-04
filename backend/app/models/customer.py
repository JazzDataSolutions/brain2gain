# backend/app/models/customer.py
from sqlalchemy import Column, Integer, String
from sqlalchemy_utils import EmailType
from app.core.database import Base
from .mixins import TimestampMixin

class Customer(Base, TimestampMixin):
    __tablename__ = "customers"

    customer_id = Column(Integer, primary_key=True, index=True)
    first_name  = Column(String, nullable=False)
    last_name   = Column(String, nullable=False)
    email       = Column(EmailType, unique=True, index=True, nullable=False)
    phone       = Column(String, nullable=True)

    orders = relationship("SalesOrder", back_populates="customer", lazy="selectin")

