"""add_event_store_table

Revision ID: 2024121200
Revises: 2024061001_add_top_products_view
Create Date: 2024-12-12 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2024121200'
down_revision = '2024061001_add_top_products_view'
branch_labels = None
depends_on = None


def upgrade():
    # Create event_store table
    op.create_table(
        'event_store',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('aggregate_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('aggregate_type', sa.String(length=50), nullable=False),
        sa.Column('data', sa.Text(), nullable=False),
        sa.Column('metadata', sa.Text(), nullable=False),
        sa.Column('occurred_at', sa.DateTime(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, default=1),
        sa.Column('processed', sa.Boolean(), nullable=False, default=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for performance
    op.create_index('ix_event_store_event_type', 'event_store', ['event_type'])
    op.create_index('ix_event_store_aggregate_id', 'event_store', ['aggregate_id'])
    op.create_index('ix_event_store_aggregate_type', 'event_store', ['aggregate_type'])
    op.create_index('ix_event_store_occurred_at', 'event_store', ['occurred_at'])
    op.create_index('ix_event_store_processed', 'event_store', ['processed'])
    
    # Create composite index for aggregate queries
    op.create_index(
        'ix_event_store_aggregate_composite', 
        'event_store', 
        ['aggregate_id', 'aggregate_type', 'occurred_at']
    )
    
    # Create index for unprocessed events
    op.create_index(
        'ix_event_store_unprocessed_events', 
        'event_store', 
        ['processed', 'occurred_at']
    )


def downgrade():
    # Drop indexes
    op.drop_index('ix_event_store_unprocessed_events', 'event_store')
    op.drop_index('ix_event_store_aggregate_composite', 'event_store')
    op.drop_index('ix_event_store_processed', 'event_store')
    op.drop_index('ix_event_store_occurred_at', 'event_store')
    op.drop_index('ix_event_store_aggregate_type', 'event_store')
    op.drop_index('ix_event_store_aggregate_id', 'event_store')
    op.drop_index('ix_event_store_event_type', 'event_store')
    
    # Drop table
    op.drop_table('event_store')