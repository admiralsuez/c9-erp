"""Add parent_id to inventory_items and serial_number import support.

Adds:
- inventory_items.parent_id (self-referencing FK for parent SKU variants)
- idx_inventory_parent index
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "8d3fa968f204"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = [c["name"] for c in inspector.get_columns("inventory_items")]

    if "parent_id" not in cols:
        op.add_column("inventory_items",
            sa.Column("parent_id", sa.Integer(), sa.ForeignKey("inventory_items.id"), nullable=True))
        op.create_index("idx_inventory_parent", "inventory_items", ["parent_id"])


def downgrade() -> None:
    op.drop_index("idx_inventory_parent", table_name="inventory_items")
    op.drop_column("inventory_items", "parent_id")
