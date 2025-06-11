"""Add materialized view for top products

Revision ID: 2024061001
Revises: 2024061000
Create Date: 2024-06-10 00:01:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2024061001'
down_revision = '2024061000'
branch_labels = None
depends_on = None


def upgrade():
    """Create materialized view for top products and refresh function."""
    
    # Create materialized view for top products
    op.execute("""
        CREATE MATERIALIZED VIEW mv_top_products AS
        SELECT 
            p.product_id,
            p.name,
            p.sku,
            COUNT(si.so_id) as total_sold,
            SUM(si.qty) as units_sold,
            SUM(si.qty * si.unit_price) as revenue,
            AVG(si.unit_price) as avg_price,
            MAX(so.order_date) as last_sold_date
        FROM product p
        JOIN salesitem si ON p.product_id = si.product_id
        JOIN salesorder so ON si.so_id = so.so_id
        WHERE so.order_date >= CURRENT_DATE - INTERVAL '30 days'
          AND so.status = 'COMPLETED'
        GROUP BY p.product_id, p.name, p.sku
        ORDER BY revenue DESC;
    """)
    
    # Create unique index on materialized view for better performance
    op.execute("""
        CREATE UNIQUE INDEX idx_mv_top_products_product_id 
        ON mv_top_products (product_id);
    """)
    
    # Create index on revenue for sorting
    op.execute("""
        CREATE INDEX idx_mv_top_products_revenue 
        ON mv_top_products (revenue DESC);
    """)
    
    # Create function to refresh the materialized view
    op.execute("""
        CREATE OR REPLACE FUNCTION refresh_top_products()
        RETURNS void AS $$
        BEGIN
            REFRESH MATERIALIZED VIEW CONCURRENTLY mv_top_products;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create a function to get top products with fallback
    op.execute("""
        CREATE OR REPLACE FUNCTION get_top_products(limit_count INTEGER DEFAULT 10)
        RETURNS TABLE(
            product_id INTEGER,
            name TEXT,
            sku TEXT,
            total_sold BIGINT,
            units_sold BIGINT,
            revenue NUMERIC,
            avg_price NUMERIC,
            last_sold_date TIMESTAMP
        ) AS $$
        BEGIN
            -- Try to return from materialized view first
            RETURN QUERY
            SELECT 
                mv.product_id,
                mv.name,
                mv.sku,
                mv.total_sold,
                mv.units_sold,
                mv.revenue,
                mv.avg_price,
                mv.last_sold_date
            FROM mv_top_products mv
            LIMIT limit_count;
            
            -- If no results, fall back to live query
            IF NOT FOUND THEN
                RETURN QUERY
                SELECT 
                    p.product_id,
                    p.name,
                    p.sku,
                    COUNT(si.so_id)::BIGINT as total_sold,
                    COALESCE(SUM(si.qty), 0)::BIGINT as units_sold,
                    COALESCE(SUM(si.qty * si.unit_price), 0) as revenue,
                    AVG(si.unit_price) as avg_price,
                    MAX(so.order_date) as last_sold_date
                FROM product p
                LEFT JOIN salesitem si ON p.product_id = si.product_id
                LEFT JOIN salesorder so ON si.so_id = so.so_id 
                    AND so.order_date >= CURRENT_DATE - INTERVAL '30 days'
                    AND so.status = 'COMPLETED'
                WHERE p.status = 'ACTIVE'
                GROUP BY p.product_id, p.name, p.sku
                ORDER BY revenue DESC
                LIMIT limit_count;
            END IF;
        END;
        $$ LANGUAGE plpgsql;
    """)


def downgrade():
    """Drop materialized view and related functions."""
    
    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS get_top_products(INTEGER);")
    op.execute("DROP FUNCTION IF EXISTS refresh_top_products();")
    
    # Drop materialized view (indexes will be dropped automatically)
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_top_products;")