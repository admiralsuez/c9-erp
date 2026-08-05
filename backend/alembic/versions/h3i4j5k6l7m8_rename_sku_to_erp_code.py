"""Rename sku column to erp_code in inventory_items

Revision ID: h3i4j5k6l7m8
Revises: g2b3c4d5e6f7
Create Date: 2026-08-05 08:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'h3i4j5k6l7m8'
down_revision: Union[str, Sequence[str], None] = 'g2b3c4d5e6f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table: str, column: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = [c["name"] for c in inspector.get_columns(table)]
    return column in cols


def upgrade() -> None:
    """Upgrade schema - rename sku to erp_code."""
    # Only rename if sku exists and erp_code doesn't
    if _column_exists('inventory_items', 'sku') and not _column_exists('inventory_items', 'erp_code'):
        # PostgreSQL: use ALTER TABLE RENAME COLUMN
        op.execute('ALTER TABLE inventory_items RENAME COLUMN sku TO erp_code')
        # Rename the unique constraint
        op.execute('ALTER TABLE inventory_items RENAME CONSTRAINT uq_inventory_sku TO uq_inventory_erp_code')
        # Rename the index
        op.execute('ALTER INDEX idx_inventory_sku RENAME TO idx_inventory_erp_code')


def downgrade() -> None:
    """Downgrade schema - rename erp_code back to sku."""
    if _column_exists('inventory_items', 'erp_code') and not _column_exists('inventory_items', 'sku'):
        op.execute('ALTER TABLE inventory_items RENAME COLUMN erp_code TO sku')
        op.execute('ALTER TABLE inventory_items RENAME CONSTRAINT uq_inventory_erp_code TO uq_inventory_sku')
        op.execute('ALTER INDEX idx_inventory_erp_code RENAME TO idx_inventory_sku')
