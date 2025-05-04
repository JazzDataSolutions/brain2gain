# backend/app/models/product.py
from sqlalchemy import Column, Integer, String, Numeric, CheckConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base
from .mixins import TimestampMixin
from .enums import ProductStatus

class Product(Base, TimestampMixin):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("unit_price >= 0", name="ck_product_unit_price_non_negative"),
    )

    product_id = Column(Integer, primary_key=True, index=True)
    sku        = Column(String, unique=True, index=True, nullable=False)
    name       = Column(String, nullable=False)
    unit_price = Column(Numeric(10,2), nullable=False)
    status     = Column(Enum(ProductStatus), nullable=False, default=ProductStatus.ACTIVE)

    sales_items = relationship(
        "SalesItem", back_populates="product", lazy="selectin"
    )

