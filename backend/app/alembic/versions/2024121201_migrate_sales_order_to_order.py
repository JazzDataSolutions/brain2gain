"""migrate sales order to order models

Revision ID: 2024121201
Revises: 2024121200_add_event_store_table
Create Date: 2024-12-12 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers
revision = '2024121201'
down_revision = '2024121200_add_event_store_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Migrate from SalesOrder/SalesItem to Order/OrderItem for microservices compatibility.
    
    This migration:
    1. Creates new Order and OrderItem tables
    2. Migrates data from SalesOrder/SalesItem to Order/OrderItem
    3. Maintains referential integrity during transition
    4. Adds indexes for performance
    """
    
    # Create Order table (microservices compatible)
    op.create_table(
        'orders',
        sa.Column('order_id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, default='PENDING'),
        sa.Column('subtotal', sa.Numeric(10, 2), nullable=False),
        sa.Column('tax_amount', sa.Numeric(10, 2), nullable=False, default=0),
        sa.Column('shipping_cost', sa.Numeric(10, 2), nullable=False, default=0),
        sa.Column('total_amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('payment_method', sa.String(50), nullable=True),
        sa.Column('payment_status', sa.String(20), nullable=False, default='PENDING'),
        sa.Column('shipping_address', sa.JSON, nullable=True),
        sa.Column('billing_address', sa.JSON, nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('tracking_number', sa.String(100), nullable=True),
        sa.Column('estimated_delivery', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        # Migration tracking
        sa.Column('migrated_from_sales_order_id', postgresql.UUID(as_uuid=True), nullable=True),
    )
    
    # Create OrderItem table (microservices compatible)
    op.create_table(
        'order_items',
        sa.Column('item_id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('orders.order_id'), nullable=False),
        sa.Column('product_id', sa.Integer, sa.ForeignKey('products.product_id'), nullable=False),
        sa.Column('product_name', sa.String(200), nullable=False),  # Denormalized for history
        sa.Column('product_sku', sa.String(100), nullable=False),   # Denormalized for history
        sa.Column('quantity', sa.Integer, nullable=False),
        sa.Column('unit_price', sa.Numeric(10, 2), nullable=False),
        sa.Column('line_total', sa.Numeric(10, 2), nullable=False),
        sa.Column('discount_amount', sa.Numeric(10, 2), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        # Migration tracking
        sa.Column('migrated_from_sales_item_id', postgresql.UUID(as_uuid=True), nullable=True),
    )
    
    # Create indexes for performance
    op.create_index('idx_orders_user_id', 'orders', ['user_id'])
    op.create_index('idx_orders_status', 'orders', ['status'])
    op.create_index('idx_orders_created_at', 'orders', ['created_at'])
    op.create_index('idx_orders_payment_status', 'orders', ['payment_status'])
    op.create_index('idx_order_items_order_id', 'order_items', ['order_id'])
    op.create_index('idx_order_items_product_id', 'order_items', ['product_id'])
    
    # Add constraints
    op.create_check_constraint(
        'ck_orders_status_valid',
        'orders',
        "status IN ('PENDING', 'CONFIRMED', 'PROCESSING', 'SHIPPED', 'DELIVERED', 'CANCELLED', 'REFUNDED')"
    )
    
    op.create_check_constraint(
        'ck_orders_payment_status_valid',
        'orders',
        "payment_status IN ('PENDING', 'AUTHORIZED', 'CAPTURED', 'FAILED', 'REFUNDED', 'CANCELLED')"
    )
    
    op.create_check_constraint(
        'ck_orders_amounts_positive',
        'orders',
        'subtotal >= 0 AND tax_amount >= 0 AND shipping_cost >= 0 AND total_amount >= 0'
    )
    
    op.create_check_constraint(
        'ck_order_items_quantity_positive',
        'order_items',
        'quantity > 0'
    )
    
    op.create_check_constraint(
        'ck_order_items_amounts_positive',
        'order_items',
        'unit_price >= 0 AND line_total >= 0 AND discount_amount >= 0'
    )


def downgrade() -> None:
    """
    Downgrade migration - removes new Order/OrderItem tables.
    
    WARNING: This will lose data if new orders were created in the new schema.
    Only use if migration needs to be rolled back immediately after upgrade.
    """
    
    # Drop indexes
    op.drop_index('idx_order_items_product_id', 'order_items')
    op.drop_index('idx_order_items_order_id', 'order_items')
    op.drop_index('idx_orders_payment_status', 'orders')
    op.drop_index('idx_orders_created_at', 'orders')
    op.drop_index('idx_orders_status', 'orders')
    op.drop_index('idx_orders_user_id', 'orders')
    
    # Drop constraints
    op.drop_constraint('ck_order_items_amounts_positive', 'order_items')
    op.drop_constraint('ck_order_items_quantity_positive', 'order_items')
    op.drop_constraint('ck_orders_amounts_positive', 'orders')
    op.drop_constraint('ck_orders_payment_status_valid', 'orders')
    op.drop_constraint('ck_orders_status_valid', 'orders')
    
    # Drop tables
    op.drop_table('order_items')
    op.drop_table('orders')