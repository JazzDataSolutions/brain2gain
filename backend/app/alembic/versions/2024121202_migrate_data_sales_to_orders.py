"""migrate data from sales_orders to orders

Revision ID: 2024121202
Revises: 2024121201_migrate_sales_order_to_order
Create Date: 2024-12-12 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers
revision = '2024121202'
down_revision = '2024121201_migrate_sales_order_to_order'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Migrate existing data from SalesOrder/SalesItem to Order/OrderItem tables.
    
    This migration:
    1. Copies all SalesOrder data to Order table with field mapping
    2. Copies all SalesItem data to OrderItem table with field mapping
    3. Maintains relationships and referential integrity
    4. Tracks migration with reference fields
    """
    
    # Get database connection
    connection = op.get_bind()
    
    # Check if source tables exist
    inspector = sa.inspect(connection)
    tables = inspector.get_table_names()
    
    if 'sales_orders' not in tables:
        print("No sales_orders table found - skipping data migration")
        return
    
    if 'sales_items' not in tables:
        print("No sales_items table found - skipping sales items migration")
    
    # Migrate SalesOrder data to Order table
    print("Migrating SalesOrder data to Order table...")
    
    migrate_orders_sql = text("""
        INSERT INTO orders (
            order_id,
            user_id,
            status,
            subtotal,
            tax_amount,
            shipping_cost,
            total_amount,
            payment_method,
            payment_status,
            shipping_address,
            notes,
            created_at,
            updated_at,
            migrated_from_sales_order_id
        )
        SELECT 
            so.order_id,
            so.user_id,
            CASE 
                WHEN so.status = 'pending' THEN 'PENDING'
                WHEN so.status = 'confirmed' THEN 'CONFIRMED'
                WHEN so.status = 'processing' THEN 'PROCESSING'
                WHEN so.status = 'shipped' THEN 'SHIPPED'
                WHEN so.status = 'delivered' THEN 'DELIVERED'
                WHEN so.status = 'cancelled' THEN 'CANCELLED'
                ELSE 'PENDING'
            END as status,
            COALESCE(so.subtotal, 0) as subtotal,
            COALESCE(so.tax, 0) as tax_amount,
            COALESCE(so.shipping_cost, 0) as shipping_cost,
            COALESCE(so.total, so.subtotal, 0) as total_amount,
            so.payment_method,
            CASE 
                WHEN so.payment_status = 'pending' THEN 'PENDING'
                WHEN so.payment_status = 'paid' THEN 'CAPTURED'
                WHEN so.payment_status = 'failed' THEN 'FAILED'
                WHEN so.payment_status = 'refunded' THEN 'REFUNDED'
                ELSE 'PENDING'
            END as payment_status,
            CASE 
                WHEN so.shipping_address IS NOT NULL THEN 
                    json_build_object(
                        'name', COALESCE(so.customer_name, ''),
                        'street', COALESCE(so.shipping_address, ''),
                        'city', COALESCE(so.shipping_city, ''),
                        'state', COALESCE(so.shipping_state, ''),
                        'zip_code', COALESCE(so.shipping_zip, ''),
                        'country', COALESCE(so.shipping_country, 'Colombia')
                    )
                ELSE NULL
            END as shipping_address,
            so.notes,
            so.created_at,
            COALESCE(so.updated_at, so.created_at) as updated_at,
            so.order_id as migrated_from_sales_order_id
        FROM sales_orders so
        WHERE NOT EXISTS (
            SELECT 1 FROM orders o WHERE o.migrated_from_sales_order_id = so.order_id
        )
    """)
    
    try:
        result = connection.execute(migrate_orders_sql)
        orders_migrated = result.rowcount
        print(f"Successfully migrated {orders_migrated} orders")
    except Exception as e:
        print(f"Error migrating orders: {e}")
        raise
    
    # Migrate SalesItem data to OrderItem table (if sales_items table exists)
    if 'sales_items' in tables:
        print("Migrating SalesItem data to OrderItem table...")
        
        migrate_items_sql = text("""
            INSERT INTO order_items (
                item_id,
                order_id,
                product_id,
                product_name,
                product_sku,
                quantity,
                unit_price,
                line_total,
                discount_amount,
                created_at,
                migrated_from_sales_item_id
            )
            SELECT 
                si.sales_item_id as item_id,
                o.order_id,
                si.product_id,
                COALESCE(si.product_name, p.name, 'Product') as product_name,
                COALESCE(si.product_sku, p.sku, 'SKU') as product_sku,
                si.quantity,
                si.unit_price,
                COALESCE(si.line_total, si.quantity * si.unit_price) as line_total,
                COALESCE(si.discount, 0) as discount_amount,
                si.created_at,
                si.sales_item_id as migrated_from_sales_item_id
            FROM sales_items si
            JOIN orders o ON o.migrated_from_sales_order_id = si.order_id
            LEFT JOIN products p ON p.product_id = si.product_id
            WHERE NOT EXISTS (
                SELECT 1 FROM order_items oi WHERE oi.migrated_from_sales_item_id = si.sales_item_id
            )
        """)
        
        try:
            result = connection.execute(migrate_items_sql)
            items_migrated = result.rowcount
            print(f"Successfully migrated {items_migrated} order items")
        except Exception as e:
            print(f"Error migrating order items: {e}")
            raise
    
    # Update order totals based on migrated items
    print("Updating order totals from migrated items...")
    
    update_totals_sql = text("""
        UPDATE orders SET 
            subtotal = COALESCE(item_totals.subtotal, 0),
            total_amount = COALESCE(item_totals.subtotal, 0) + tax_amount + shipping_cost
        FROM (
            SELECT 
                oi.order_id,
                SUM(oi.line_total - oi.discount_amount) as subtotal
            FROM order_items oi
            GROUP BY oi.order_id
        ) as item_totals
        WHERE orders.order_id = item_totals.order_id
        AND orders.migrated_from_sales_order_id IS NOT NULL
    """)
    
    try:
        result = connection.execute(update_totals_sql)
        totals_updated = result.rowcount
        print(f"Updated totals for {totals_updated} orders")
    except Exception as e:
        print(f"Error updating order totals: {e}")
        # Don't raise - this is not critical
    
    print("Data migration completed successfully!")


def downgrade() -> None:
    """
    Downgrade data migration - remove migrated data from new tables.
    
    This removes all data that was migrated from SalesOrder/SalesItem tables.
    Data created directly in Order/OrderItem tables will be preserved.
    """
    
    connection = op.get_bind()
    
    print("Removing migrated order items...")
    
    # Remove migrated order items
    delete_items_sql = text("""
        DELETE FROM order_items 
        WHERE migrated_from_sales_item_id IS NOT NULL
    """)
    
    try:
        result = connection.execute(delete_items_sql)
        items_removed = result.rowcount
        print(f"Removed {items_removed} migrated order items")
    except Exception as e:
        print(f"Error removing migrated order items: {e}")
        raise
    
    print("Removing migrated orders...")
    
    # Remove migrated orders
    delete_orders_sql = text("""
        DELETE FROM orders 
        WHERE migrated_from_sales_order_id IS NOT NULL
    """)
    
    try:
        result = connection.execute(delete_orders_sql)
        orders_removed = result.rowcount
        print(f"Removed {orders_removed} migrated orders")
    except Exception as e:
        print(f"Error removing migrated orders: {e}")
        raise
    
    print("Data migration rollback completed!")