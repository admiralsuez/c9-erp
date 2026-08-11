"""add new fields phase 9

Revision ID: phase_9_add_new_fields
Revises: 
Create Date: 2026-08-11 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'phase_9_add_new_fields'
down_revision = 'bd0c719effb1'  # adjust to match your latest migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add challan_book_number to documents table
    op.add_column('documents', sa.Column('challan_book_number', sa.String(50), nullable=True))
    
    # Add return_reason and return_status to order_items table
    op.add_column('order_items', sa.Column('return_reason', sa.String(50), nullable=True))
    op.add_column('order_items', sa.Column('return_status', sa.String(50), nullable=True))


def downgrade() -> None:
    # Remove columns
    op.drop_column('documents', 'challan_book_number')
    op.drop_column('order_items', 'return_reason')
    op.drop_column('order_items', 'return_status')
