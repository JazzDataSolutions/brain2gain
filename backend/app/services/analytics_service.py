# backend/app/services/analytics_service.py

from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from sqlmodel import Session, select, func, and_, or_
from sqlalchemy import text

from ..models import (
    Transaction, TransactionType, Customer, Product, SalesOrder, 
    SalesItem, OrderStatus, Stock, Cart, CartItem
)


class AnalyticsService:
    """Service for calculating business analytics and KPIs"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ─── REVENUE METRICS ──────────────────────────────────────────────────────
    
    def get_total_revenue(
        self, 
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None
    ) -> Decimal:
        """Calculate total revenue for a given period"""
        query = select(func.sum(Transaction.amount)).where(
            Transaction.tx_type == TransactionType.SALE,
            Transaction.paid == True
        )
        
        if start_date:
            query = query.where(Transaction.created_at >= start_date)
        if end_date:
            query = query.where(Transaction.created_at <= end_date)
            
        result = self.db.exec(query).first()
        return result or Decimal(0)
    
    def get_daily_revenue(self, target_date: date) -> Decimal:
        """Calculate revenue for a specific day"""
        start_datetime = datetime.combine(target_date, datetime.min.time())
        end_datetime = datetime.combine(target_date, datetime.max.time())
        
        return self.get_total_revenue(start_datetime, end_datetime)
    
    def get_monthly_revenue(self, year: int, month: int) -> Decimal:
        """Calculate revenue for a specific month"""
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(seconds=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(seconds=1)
            
        return self.get_total_revenue(start_date, end_date)
    
    def get_revenue_growth_rate(self, period_days: int = 30) -> float:
        """Calculate revenue growth rate comparing two periods"""
        end_date = datetime.utcnow()
        start_current = end_date - timedelta(days=period_days)
        start_previous = start_current - timedelta(days=period_days)
        end_previous = start_current
        
        current_revenue = self.get_total_revenue(start_current, end_date)
        previous_revenue = self.get_total_revenue(start_previous, end_previous)
        
        if previous_revenue == 0:
            return 0.0
            
        growth_rate = float((current_revenue - previous_revenue) / previous_revenue * 100)
        return round(growth_rate, 2)
    
    # ─── ORDER METRICS ────────────────────────────────────────────────────────
    
    def get_average_order_value(
        self, 
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None
    ) -> Decimal:
        """Calculate Average Order Value (AOV)"""
        # Calculate total revenue from completed orders
        revenue_query = select(func.sum(SalesItem.qty * SalesItem.unit_price)).join(
            SalesOrder
        ).where(SalesOrder.status == OrderStatus.COMPLETED)
        
        # Count completed orders
        orders_query = select(func.count(SalesOrder.so_id)).where(
            SalesOrder.status == OrderStatus.COMPLETED
        )
        
        if start_date:
            revenue_query = revenue_query.where(SalesOrder.order_date >= start_date)
            orders_query = orders_query.where(SalesOrder.order_date >= start_date)
        if end_date:
            revenue_query = revenue_query.where(SalesOrder.order_date <= end_date)
            orders_query = orders_query.where(SalesOrder.order_date <= end_date)
        
        total_revenue = self.db.exec(revenue_query).first() or Decimal(0)
        total_orders = self.db.exec(orders_query).first() or 0
        
        if total_orders == 0:
            return Decimal(0)
            
        return round(total_revenue / total_orders, 2)
    
    def get_order_metrics(self) -> Dict:
        """Get comprehensive order metrics"""
        today = datetime.utcnow().date()
        month_start = datetime(today.year, today.month, 1)
        
        # Orders today
        orders_today = self.db.exec(
            select(func.count(SalesOrder.so_id)).where(
                func.date(SalesOrder.order_date) == today
            )
        ).first() or 0
        
        # Orders this month
        orders_month = self.db.exec(
            select(func.count(SalesOrder.so_id)).where(
                SalesOrder.order_date >= month_start
            )
        ).first() or 0
        
        # Pending orders
        pending_orders = self.db.exec(
            select(func.count(SalesOrder.so_id)).where(
                SalesOrder.status == OrderStatus.PENDING
            )
        ).first() or 0
        
        return {
            "orders_today": orders_today,
            "orders_month": orders_month,
            "pending_orders": pending_orders,
            "average_order_value": float(self.get_average_order_value())
        }
    
    # ─── CUSTOMER METRICS ─────────────────────────────────────────────────────
    
    def get_customer_metrics(self) -> Dict:
        """Get comprehensive customer metrics"""
        # Total customers
        total_customers = self.db.exec(
            select(func.count(Customer.customer_id))
        ).first() or 0
        
        # New customers this month
        month_start = datetime(datetime.utcnow().year, datetime.utcnow().month, 1)
        new_customers_month = self.db.exec(
            select(func.count(Customer.customer_id)).where(
                Customer.created_at >= month_start
            )
        ).first() or 0
        
        # Customers with orders
        customers_with_orders = self.db.exec(
            select(func.count(func.distinct(SalesOrder.customer_id))).where(
                SalesOrder.status == OrderStatus.COMPLETED
            )
        ).first() or 0
        
        # Active customers (ordered in last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        active_customers = self.db.exec(
            select(func.count(func.distinct(SalesOrder.customer_id))).where(
                and_(
                    SalesOrder.order_date >= thirty_days_ago,
                    SalesOrder.status == OrderStatus.COMPLETED
                )
            )
        ).first() or 0
        
        return {
            "total_customers": total_customers,
            "new_customers_month": new_customers_month,
            "customers_with_orders": customers_with_orders,
            "active_customers_30d": active_customers,
            "customer_conversion_rate": round(
                (customers_with_orders / total_customers * 100) if total_customers > 0 else 0, 2
            )
        }
    
    def calculate_customer_lifetime_value(self, customer_id: int) -> Decimal:
        """Calculate CLV for a specific customer"""
        # Total revenue from customer
        total_spent = self.db.exec(
            select(func.sum(Transaction.amount)).where(
                and_(
                    Transaction.customer_id == customer_id,
                    Transaction.tx_type == TransactionType.SALE,
                    Transaction.paid == True
                )
            )
        ).first() or Decimal(0)
        
        # Number of orders
        order_count = self.db.exec(
            select(func.count(SalesOrder.so_id)).where(
                and_(
                    SalesOrder.customer_id == customer_id,
                    SalesOrder.status == OrderStatus.COMPLETED
                )
            )
        ).first() or 0
        
        # Customer lifespan in days
        customer = self.db.get(Customer, customer_id)
        if not customer:
            return Decimal(0)
            
        lifespan_days = (datetime.utcnow() - customer.created_at).days
        if lifespan_days == 0:
            lifespan_days = 1
            
        # Simple CLV calculation
        avg_order_value = total_spent / order_count if order_count > 0 else Decimal(0)
        purchase_frequency = order_count / (lifespan_days / 30) if lifespan_days > 0 else 0
        
        # Assume 24 month customer lifespan and 20% profit margin
        clv = avg_order_value * purchase_frequency * 24 * Decimal(0.2)
        
        return round(clv, 2)
    
    # ─── PRODUCT METRICS ──────────────────────────────────────────────────────
    
    def get_top_selling_products(self, limit: int = 10) -> List[Dict]:
        """Get top selling products by quantity"""
        query = (
            select(
                Product.product_id,
                Product.name,
                Product.sku,
                func.sum(SalesItem.qty).label("total_sold"),
                func.sum(SalesItem.qty * SalesItem.unit_price).label("total_revenue")
            )
            .join(SalesItem)
            .join(SalesOrder)
            .where(SalesOrder.status == OrderStatus.COMPLETED)
            .group_by(Product.product_id, Product.name, Product.sku)
            .order_by(func.sum(SalesItem.qty).desc())
            .limit(limit)
        )
        
        results = self.db.exec(query).all()
        
        return [
            {
                "product_id": row.product_id,
                "name": row.name,
                "sku": row.sku,
                "total_sold": row.total_sold,
                "total_revenue": float(row.total_revenue)
            }
            for row in results
        ]
    
    def get_inventory_metrics(self) -> Dict:
        """Get inventory-related metrics"""
        # Total products
        total_products = self.db.exec(
            select(func.count(Product.product_id))
        ).first() or 0
        
        # Low stock products (quantity < 10)
        low_stock_products = self.db.exec(
            select(func.count(Stock.stock_id)).where(Stock.quantity < 10)
        ).first() or 0
        
        # Out of stock products
        out_of_stock = self.db.exec(
            select(func.count(Stock.stock_id)).where(Stock.quantity == 0)
        ).first() or 0
        
        # Total inventory value
        total_inventory_value = self.db.exec(
            select(func.sum(Stock.quantity * Product.unit_price))
            .join(Product)
        ).first() or Decimal(0)
        
        return {
            "total_products": total_products,
            "low_stock_products": low_stock_products,
            "out_of_stock_products": out_of_stock,
            "total_inventory_value": float(total_inventory_value)
        }
    
    # ─── CONVERSION METRICS ───────────────────────────────────────────────────
    
    def get_cart_abandonment_rate(self, days: int = 30) -> float:
        """Calculate cart abandonment rate"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Total carts created
        total_carts = self.db.exec(
            select(func.count(Cart.cart_id)).where(
                Cart.created_at >= start_date
            )
        ).first() or 0
        
        # Completed orders (carts that converted)
        completed_orders = self.db.exec(
            select(func.count(SalesOrder.so_id)).where(
                and_(
                    SalesOrder.order_date >= start_date,
                    SalesOrder.status == OrderStatus.COMPLETED
                )
            )
        ).first() or 0
        
        if total_carts == 0:
            return 0.0
            
        abandonment_rate = ((total_carts - completed_orders) / total_carts) * 100
        return round(abandonment_rate, 2)
    
    # ─── FINANCIAL METRICS ────────────────────────────────────────────────────
    
    def get_financial_summary(self) -> Dict:
        """Get comprehensive financial summary"""
        today = datetime.utcnow().date()
        month_start = datetime(today.year, today.month, 1)
        year_start = datetime(today.year, 1, 1)
        
        return {
            "revenue": {
                "today": float(self.get_daily_revenue(today)),
                "month": float(self.get_total_revenue(month_start)),
                "year": float(self.get_total_revenue(year_start)),
                "growth_rate": self.get_revenue_growth_rate()
            },
            "orders": self.get_order_metrics(),
            "customers": self.get_customer_metrics(),
            "inventory": self.get_inventory_metrics(),
            "conversion": {
                "cart_abandonment_rate": self.get_cart_abandonment_rate()
            }
        }
    
    # ─── REAL-TIME METRICS ────────────────────────────────────────────────────
    
    def get_realtime_metrics(self) -> Dict:
        """Get real-time metrics for dashboard"""
        return {
            "current_revenue_today": float(self.get_daily_revenue(datetime.utcnow().date())),
            "orders_today": self.get_order_metrics()["orders_today"],
            "pending_orders": self.get_order_metrics()["pending_orders"],
            "active_carts": self.db.exec(
                select(func.count(Cart.cart_id)).where(
                    Cart.updated_at >= datetime.utcnow() - timedelta(hours=24)
                )
            ).first() or 0,
            "low_stock_alerts": self.get_inventory_metrics()["low_stock_products"],
            "timestamp": datetime.utcnow().isoformat()
        }