"""Merge phase3_vendor_addresses and merge_heads_restore_sku branches

Revision ID: merge_phase3_and_sku_heads
Revises: merge_heads_restore_sku, phase3_vendor_addresses
Create Date: 2026-08-18 08:00:00.000000

Merges the two divergent migration branches:
  - merge_heads_restore_sku (SKU column restoration and inventory stock management)
  - phase3_vendor_addresses (Vendor address hierarchy with parent_id)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'merge_phase3_and_sku_heads'
down_revision: Union[str, Sequence[str], None] = ('merge_heads_restore_sku', 'phase3_vendor_addresses')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge branches - no additional operations needed."""
    pass


def downgrade() -> None:
    """Merge downgrade is a no-op (merged branches cannot split)."""
    pass
