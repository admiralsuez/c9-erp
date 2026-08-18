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
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    # Check and add challan_book_number to documents table
    docs_cols = [c["name"] for c in inspector.get_columns("documents")]
    if "challan_book_number" not in docs_cols:
        op.add_column('documents', sa.Column('challan_book_number', sa.String(50), nullable=True))
    
    # Check and add return_reason and return_status to order_items table
    items_cols = [c["name"] for c in inspector.get_columns("order_items")]
    if "return_reason" not in items_cols:
        op.add_column('order_items', sa.Column('return_reason', sa.String(50), nullable=True))
    if "return_status" not in items_cols:
        op.add_column('order_items', sa.Column('return_status', sa.String(50), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    # Remove columns if they exist
    docs_cols = [c["name"] for c in inspector.get_columns("documents")]
    if "challan_book_number" in docs_cols:
        op.drop_column('documents', 'challan_book_number')
    
    items_cols = [c["name"] for c in inspector.get_columns("order_items")]
    if "return_reason" in items_cols:
        op.drop_column('order_items', 'return_reason')
    if "return_status" in items_cols:
        op.drop_column('order_items', 'return_status')
