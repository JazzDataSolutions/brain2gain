# backend/performance_optimizations/optimized_models.py
"""
Optimized database models with strategic indexes and performance improvements.
"""

import uuid
from typing import List, Optional
from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel, Index
from datetime import datetime, date
from decimal import Decimal
from enum import Enum

# ─── OPTIMIZED PRODUCT MODEL ──────────────────────────────────────────────

class Product(SQLModel, table=True):
    __tablename__ = "product"
    
    product_id: Optional[int] = Field(default=None, primary_key=True)
    sku: str = Field(unique=True, index=True, nullable=False, max_length=50)
    name: str = Field(nullable=False, max_length=255, index=True)  # ✅ Índice para búsquedas
    unit_price: Decimal = Field(ge=0, nullable=False, index=True)  # ✅ Índice para filtros de precio
    status: str = Field(default="ACTIVE", nullable=False, index=True)  # ✅ Índice para filtros de estado
    category_id: Optional[int] = Field(foreign_key="category.id", index=True)  # ✅ Índice FK
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False, index=True)  # ✅ Índice para ordenamiento temporal
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    
    # Full-text search field (PostgreSQL specific)
    search_vector: Optional[str] = Field(sa_column_kwargs={"type_": "tsvector"})

    # Relationships with optimized loading
    stock: "Stock" = Relationship(
        back_populates="product", 
        sa_relationship_kwargs={
            "uselist": False,
            "lazy": "select"  # Eager loading for frequently accessed data
        }
    )
    sales_items: List["SalesItem"] = Relationship(
        back_populates="product",
        sa_relationship_kwargs={"lazy": "dynamic"}  # Dynamic loading for large collections
    )
    
    # Composite indexes for common query patterns
    __table_args__ = (
        Index('idx_product_status_price', 'status', 'unit_price'),
        Index('idx_product_created_status', 'created_at', 'status'),
        Index('idx_product_name_search', 'name', postgresql_using='gin'),
        Index('idx_product_search_vector', 'search_vector', postgresql_using='gin'),
    )


# ─── OPTIMIZED CUSTOMER MODEL ─────────────────────────────────────────────

class Customer(SQLModel, table=True):
    __tablename__ = "customer"
    
    customer_id: Optional[int] = Field(default=None, primary_key=True)
    first_name: str = Field(nullable=False, max_length=100, index=True)
    last_name: str = Field(nullable=False, max_length=100, index=True)
    email: EmailStr = Field(unique=True, index=True, nullable=False)
    phone: Optional[str] = Field(max_length=20, index=True)  # ✅ Índice para búsquedas por teléfono
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    
    # Customer segmentation fields
    total_orders: int = Field(default=0, index=True)  # ✅ Para segmentación de clientes
    total_spent: Decimal = Field(default=0, ge=0, index=True)  # ✅ Para análisis de valor
    last_order_date: Optional[datetime] = Field(index=True)  # ✅ Para análisis de recencia
    
    orders: List["SalesOrder"] = Relationship(
        back_populates="customer",
        sa_relationship_kwargs={"lazy": "dynamic", "order_by": "desc(SalesOrder.order_date)"}
    )
    
    __table_args__ = (
        Index('idx_customer_name', 'first_name', 'last_name'),
        Index('idx_customer_value', 'total_spent', 'total_orders'),
        Index('idx_customer_activity', 'last_order_date', 'created_at'),
    )


# ─── OPTIMIZED SALES ORDER MODEL ──────────────────────────────────────────

class SalesOrder(SQLModel, table=True):
    __tablename__ = "salesorder"
    
    so_id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customer.customer_id", nullable=False, index=True)
    order_date: datetime = Field(default_factory=datetime.utcnow, nullable=False, index=True)
    status: str = Field(default="PENDING", nullable=False, index=True)
    total_amount: Decimal = Field(ge=0, nullable=False, index=True)  # ✅ Campo calculado para performance
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    
    customer: "Customer" = Relationship(back_populates="orders")
    items: List["SalesItem"] = Relationship(
        back_populates="order",
        sa_relationship_kwargs={"lazy": "selectin"}  # Eager loading for order items
    )
    
    __table_args__ = (
        Index('idx_order_customer_date', 'customer_id', 'order_date'),
        Index('idx_order_status_date', 'status', 'order_date'),
        Index('idx_order_amount_date', 'total_amount', 'order_date'),
    )


# ─── OPTIMIZED STOCK MODEL ────────────────────────────────────────────────

class Stock(SQLModel, table=True):
    __tablename__ = "stock"
    
    stock_id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="product.product_id", unique=True, nullable=False)
    quantity: int = Field(ge=0, nullable=False, index=True)  # ✅ Índice para filtros de stock
    reserved_quantity: int = Field(default=0, ge=0)  # ✅ Para reservas de inventario
    reorder_level: int = Field(default=10, ge=0, index=True)  # ✅ Para alertas de stock bajo
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    
    product: "Product" = Relationship(back_populates="stock")
    
    __table_args__ = (
        Index('idx_stock_low_inventory', 'quantity', 'reorder_level'),
        Index('idx_stock_availability', 'quantity', 'reserved_quantity'),
    )


# ─── AUDIT TRAIL MODEL ────────────────────────────────────────────────────

class AuditLog(SQLModel, table=True):
    """Audit trail for sensitive operations with optimized indexing."""
    __tablename__ = "audit_log"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    table_name: str = Field(nullable=False, max_length=50, index=True)
    record_id: str = Field(nullable=False, index=True)
    action: str = Field(nullable=False, max_length=20, index=True)  # INSERT, UPDATE, DELETE
    user_id: Optional[str] = Field(max_length=50, index=True)
    changes: Optional[str] = None  # JSON string of changes
    timestamp: datetime = Field(default_factory=datetime.utcnow, nullable=False, index=True)
    ip_address: Optional[str] = Field(max_length=45)
    
    __table_args__ = (
        Index('idx_audit_table_record', 'table_name', 'record_id'),
        Index('idx_audit_user_time', 'user_id', 'timestamp'),
        Index('idx_audit_action_time', 'action', 'timestamp'),
    )


# ─── MATERIALIZED VIEW FOR ANALYTICS ──────────────────────────────────────

class ProductAnalytics(SQLModel, table=True):
    """Materialized view for product performance analytics."""
    __tablename__ = "product_analytics"
    
    product_id: int = Field(primary_key=True)
    sku: str = Field(nullable=False)
    name: str = Field(nullable=False)
    total_sales: Decimal = Field(default=0)
    total_quantity_sold: int = Field(default=0)
    avg_order_value: Decimal = Field(default=0)
    last_sale_date: Optional[datetime] = None
    days_since_last_sale: Optional[int] = None
    velocity_score: Decimal = Field(default=0)  # Sales velocity metric
    
    __table_args__ = (
        Index('idx_analytics_velocity', 'velocity_score'),
        Index('idx_analytics_sales', 'total_sales'),
        Index('idx_analytics_activity', 'last_sale_date', 'days_since_last_sale'),
    )