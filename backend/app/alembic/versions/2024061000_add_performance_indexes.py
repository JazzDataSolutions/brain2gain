"""Add performance indexes

Revision ID: 2024061000
Revises: 1a31ce608336
Create Date: 2024-06-10 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2024061000"
down_revision = "1a31ce608336"
branch_labels = None
depends_on = None


def upgrade():
    """Add critical performance indexes."""

    # Product indexes for faster queries
    op.create_index(
        "idx_product_status_active",
        "product",
        ["status"],
        postgresql_where=sa.text("status = 'ACTIVE'"),
    )

    # SalesOrder indexes for customer queries and date sorting
    op.create_index(
        "idx_salesorder_customer_date",
        "salesorder",
        ["customer_id", "order_date"],
        postgresql_using="btree",
    )

    op.create_index("idx_salesorder_status", "salesorder", ["status"])

    # SalesItem indexes for order item lookups
    op.create_index("idx_salesitem_order", "salesitem", ["so_id"])

    op.create_index("idx_salesitem_product", "salesitem", ["product_id"])

    # Cart indexes for session and user lookups
    op.create_index("idx_cart_user", "cart", ["user_id"])

    # Transaction indexes for financial queries
    op.create_index(
        "idx_transaction_customer_date",
        "transaction",
        ["customer_id", "created_at"],
        postgresql_using="btree",
    )

    op.create_index("idx_transaction_type_paid", "transaction", ["tx_type", "paid"])

    op.create_index(
        "idx_transaction_due_date",
        "transaction",
        ["due_date"],
        postgresql_where=sa.text("paid = false AND due_date IS NOT NULL"),
    )

    # Stock index for product lookups (product_id should already be unique)
    # Adding updated_at for recent stock changes
    op.create_index("idx_stock_updated", "stock", ["updated_at"])


def downgrade():
    """Remove performance indexes."""

    # Drop all created indexes
    op.drop_index("idx_product_status_active", table_name="product")
    op.drop_index("idx_salesorder_customer_date", table_name="salesorder")
    op.drop_index("idx_salesorder_status", table_name="salesorder")
    op.drop_index("idx_salesitem_order", table_name="salesitem")
    op.drop_index("idx_salesitem_product", table_name="salesitem")
    op.drop_index("idx_cart_user", table_name="cart")
    op.drop_index("idx_transaction_customer_date", table_name="transaction")
    op.drop_index("idx_transaction_type_paid", table_name="transaction")
    op.drop_index("idx_transaction_due_date", table_name="transaction")
    op.drop_index("idx_stock_updated", table_name="stock")
