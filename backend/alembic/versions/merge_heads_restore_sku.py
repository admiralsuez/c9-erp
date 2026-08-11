"""Merge migration branches and restore sku column

Revision ID: merge_heads_restore_sku
Revises: h3i4j5k6l7m8, add_inventory_stock_management
Create Date: 2026-08-11 15:00:00.000000

The migration history diverged from bd0c719effb1 into two branches:
  - h3i4j5k6l7m8 (sku -> erp_code rename, now a no-op)
  - phase_9_add_new_fields -> add_inventory_stock_management

This revision merges them into a single head and restores the ``sku``
column name for databases where the erp_code rename was already applied
(the application model and all code use ``sku``).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'merge_heads_restore_sku'
down_revision: Union[str, Sequence[str], None] = ('h3i4j5k6l7m8', 'add_inventory_stock_management')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table: str, column: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = [c["name"] for c in inspector.get_columns(table)]
    return column in cols


def upgrade() -> None:
    """Merge branches. If a database had erp_code applied, restore sku."""
    if _column_exists('inventory_items', 'erp_code') and not _column_exists('inventory_items', 'sku'):
        op.execute('ALTER TABLE inventory_items RENAME COLUMN erp_code TO sku')
        # Rename constraint/index back if they were renamed (PostgreSQL only)
        bind = op.get_bind()
        inspector = sa.inspect(bind)
        for idx in inspector.get_indexes('inventory_items'):
            if idx['name'] == 'idx_inventory_erp_code':
                op.execute('ALTER INDEX idx_inventory_erp_code RENAME TO idx_inventory_sku')
        for con in inspector.get_unique_constraints('inventory_items'):
            if con['name'] == 'uq_inventory_erp_code':
                op.execute('ALTER TABLE inventory_items RENAME CONSTRAINT uq_inventory_erp_code TO uq_inventory_sku')


def downgrade() -> None:
    """Merge downgrade is a no-op (squashed branches cannot split)."""
    pass
