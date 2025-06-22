"""add payment and refund tables

Revision ID: 2024121203
Revises: 2024121202_migrate_data_sales_to_orders
Create Date: 2024-12-12 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers
revision = '2024121203'
down_revision = '2024121202_migrate_data_sales_to_orders'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create Payment and Refund tables for comprehensive payment processing.
    
    This migration creates:
    1. Payment table for tracking all payment transactions
    2. Refund table for tracking refunds and chargebacks
    3. Indexes for performance optimization
    4. Constraints for data integrity
    """
    
    # Create Payment table
    op.create_table(
        'payments',
        sa.Column('payment_id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('orders.order_id'), nullable=False),
        
        # Payment details
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, default='MXN'),
        sa.Column('payment_method', sa.String(50), nullable=False),  # stripe, paypal, bank_transfer
        
        # Status and processing
        sa.Column('status', sa.String(20), nullable=False, default='PENDING'),
        
        # External references (gateway transaction IDs)
        sa.Column('stripe_payment_intent_id', sa.String(255), nullable=True),
        sa.Column('paypal_order_id', sa.String(255), nullable=True),
        sa.Column('gateway_transaction_id', sa.String(255), nullable=True),
        
        # Payment processing details
        sa.Column('gateway_response', sa.JSON, nullable=True),
        sa.Column('failure_reason', sa.String(500), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('authorized_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('captured_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failed_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create Refund table
    op.create_table(
        'refunds',
        sa.Column('refund_id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('payment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('payments.payment_id'), nullable=False),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('orders.order_id'), nullable=False),
        
        # Refund details
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('reason', sa.String(500), nullable=False),
        
        # Processing details
        sa.Column('gateway_refund_id', sa.String(255), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, default='PENDING'),  # PENDING, COMPLETED, FAILED
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create indexes for performance
    op.create_index('idx_payments_order_id', 'payments', ['order_id'])
    op.create_index('idx_payments_status', 'payments', ['status'])
    op.create_index('idx_payments_method', 'payments', ['payment_method'])
    op.create_index('idx_payments_created_at', 'payments', ['created_at'])
    op.create_index('idx_payments_stripe_intent', 'payments', ['stripe_payment_intent_id'])
    op.create_index('idx_payments_paypal_order', 'payments', ['paypal_order_id'])
    op.create_index('idx_payments_gateway_tx', 'payments', ['gateway_transaction_id'])
    
    op.create_index('idx_refunds_payment_id', 'refunds', ['payment_id'])
    op.create_index('idx_refunds_order_id', 'refunds', ['order_id'])
    op.create_index('idx_refunds_status', 'refunds', ['status'])
    op.create_index('idx_refunds_created_at', 'refunds', ['created_at'])
    
    # Add constraints for data integrity
    op.create_check_constraint(
        'ck_payments_status_valid',
        'payments',
        "status IN ('PENDING', 'AUTHORIZED', 'CAPTURED', 'FAILED', 'REFUNDED', 'CANCELLED')"
    )
    
    op.create_check_constraint(
        'ck_payments_method_valid',
        'payments',
        "payment_method IN ('stripe', 'paypal', 'bank_transfer', 'cash', 'card')"
    )
    
    op.create_check_constraint(
        'ck_payments_amount_positive',
        'payments',
        'amount > 0'
    )
    
    op.create_check_constraint(
        'ck_payments_currency_valid',
        'payments',
        "currency IN ('MXN', 'USD', 'EUR')"
    )
    
    op.create_check_constraint(
        'ck_refunds_status_valid',
        'refunds',
        "status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'CANCELLED')"
    )
    
    op.create_check_constraint(
        'ck_refunds_amount_positive',
        'refunds',
        'amount > 0'
    )
    
    # Add unique constraints for external IDs
    op.create_unique_constraint(
        'uq_payments_stripe_intent',
        'payments',
        ['stripe_payment_intent_id'],
        postgresql_where=sa.text('stripe_payment_intent_id IS NOT NULL')
    )
    
    op.create_unique_constraint(
        'uq_payments_paypal_order',
        'payments',
        ['paypal_order_id'],
        postgresql_where=sa.text('paypal_order_id IS NOT NULL')
    )
    
    op.create_unique_constraint(
        'uq_payments_gateway_tx',
        'payments',
        ['gateway_transaction_id'],
        postgresql_where=sa.text('gateway_transaction_id IS NOT NULL')
    )


def downgrade() -> None:
    """
    Remove Payment and Refund tables.
    
    WARNING: This will permanently delete all payment and refund data.
    """
    
    # Drop constraints
    op.drop_constraint('uq_payments_gateway_tx', 'payments')
    op.drop_constraint('uq_payments_paypal_order', 'payments')
    op.drop_constraint('uq_payments_stripe_intent', 'payments')
    
    op.drop_constraint('ck_refunds_amount_positive', 'refunds')
    op.drop_constraint('ck_refunds_status_valid', 'refunds')
    op.drop_constraint('ck_payments_currency_valid', 'payments')
    op.drop_constraint('ck_payments_amount_positive', 'payments')
    op.drop_constraint('ck_payments_method_valid', 'payments')
    op.drop_constraint('ck_payments_status_valid', 'payments')
    
    # Drop indexes
    op.drop_index('idx_refunds_created_at', 'refunds')
    op.drop_index('idx_refunds_status', 'refunds')
    op.drop_index('idx_refunds_order_id', 'refunds')
    op.drop_index('idx_refunds_payment_id', 'refunds')
    
    op.drop_index('idx_payments_gateway_tx', 'payments')
    op.drop_index('idx_payments_paypal_order', 'payments')
    op.drop_index('idx_payments_stripe_intent', 'payments')
    op.drop_index('idx_payments_created_at', 'payments')
    op.drop_index('idx_payments_method', 'payments')
    op.drop_index('idx_payments_status', 'payments')
    op.drop_index('idx_payments_order_id', 'payments')
    
    # Drop tables
    op.drop_table('refunds')
    op.drop_table('payments')