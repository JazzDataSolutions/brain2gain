# backend/app/models/sales.py
from sqlalchemy import (
    Column, Integer, ForeignKey, DateTime, Numeric,
    CheckConstraint
)
from sqlalchemy.orm import relationship
from .mixins import TimestampMixin
from .enums import OrderStatus
from app.core.database import Base

class SalesOrder(Base, TimestampMixin):
    __tablename__ = "sales_orders"

    so_id      = Column(Integer, primary_key=True, index=True)
    customer_id= Column(Integer, ForeignKey("customers.customer_id"), nullable=False)
    order_date = Column(DateTime(timezone=True), server_default=func.now())
    status     = Column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False)

    customer   = relationship("Customer", back_populates="orders", lazy="joined")
    items      = relationship(
                    "SalesItem",
                    back_populates="order",
                    cascade="all, delete-orphan",
                    lazy="selectin"
                 )

    @property
    def total_amount(self) -> Numeric:
        return sum(item.qty * item.unit_price for item in self.items)

class SalesItem(Base, TimestampMixin):
    __tablename__ = "sales_items"
    __table_args__ = (
        CheckConstraint("qty > 0", name="ck_salesitem_qty_positive"),
    )

    so_id      = Column(Integer, ForeignKey("sales_orders.so_id"), primary_key=True)
    product_id = Column(Integer, ForeignKey("products.product_id"), primary_key=True)
    qty        = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10,2), nullable=False)

    order   = relationship("SalesOrder", back_populates="items", lazy="joined")
    product = relationship("Product", back_populates="sales_items", lazy="joined")

