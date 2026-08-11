"""Add inventory stock management fields

Revision ID: add_inventory_stock_management
Revises: phase_9_add_new_fields
Create Date: 2026-08-11 10:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_inventory_stock_management'
down_revision = 'phase_9_add_new_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add stock management fields to inventory_items table
    op.add_column('inventory_items', sa.Column('expiry_date', sa.DateTime(timezone=True), nullable=True))
    op.add_column('inventory_items', sa.Column('allow_no_expiry', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('inventory_items', sa.Column('stock_status', sa.String(50), nullable=False, server_default='active'))


def downgrade() -> None:
    # Remove columns
    op.drop_column('inventory_items', 'stock_status')
    op.drop_column('inventory_items', 'allow_no_expiry')
    op.drop_column('inventory_items', 'expiry_date')
