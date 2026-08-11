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
    """Upgrade schema - rename sku to erp_code.

    NOTE: Neutralized. The application model and all code use ``sku``;
    this rename was never reflected in the model, so it would break every
    inventory query. Kept as a no-op for DBs that already stamped this
    revision. A follow-up merge migration restores ``sku`` for any DB where
    the rename was applied.
    """
    pass


def downgrade() -> None:
    """Downgrade schema - rename erp_code back to sku."""
    pass
