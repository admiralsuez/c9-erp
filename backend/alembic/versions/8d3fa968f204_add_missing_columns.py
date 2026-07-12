"""Add missing columns and indexes for backward compatibility.

Adds columns that were added to models after initial deployment:
- vendors.vendor_token_hash
- orders.approver_id
- notifications.actor_id
- inventory_items.idx_inventory_deleted_at
- orders.idx_orders_deleted_at
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision: str = "8d3fa968f204"
down_revision: Union[str, Sequence[str], None] = "abb4ff9cf8d5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = [c["name"] for c in inspector.get_columns(table)]
    return column in cols


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    # vendors.vendor_token_hash
    if not _has_column("vendors", "vendor_token_hash"):
        op.add_column("vendors", sa.Column("vendor_token_hash", sa.String(64)))
        op.create_index("idx_vendor_token_hash", "vendors", ["vendor_token_hash"])

    # orders.approver_id
    if not _has_column("orders", "approver_id"):
        op.add_column("orders", sa.Column("approver_id", sa.Integer(), sa.ForeignKey("users.id")))

    # notifications.actor_id
    if not _has_column("notifications", "actor_id"):
        op.add_column("notifications", sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id")))

    # deleted_at indexes — SQLite doesn't support CREATE INDEX IF NOT EXISTS
    if dialect == "postgresql":
        op.create_index("idx_inventory_deleted_at", "inventory_items", ["deleted_at"], unique=False, postgresql_if_not_exists=True)
        op.create_index("idx_orders_deleted_at", "orders", ["deleted_at"], unique=False, postgresql_if_not_exists=True)
    else:
        op.execute(text("CREATE INDEX IF NOT EXISTS idx_inventory_deleted_at ON inventory_items(deleted_at)"))
        op.execute(text("CREATE INDEX IF NOT EXISTS idx_orders_deleted_at ON orders(deleted_at)"))


def downgrade() -> None:
    if _has_column("notifications", "actor_id"):
        op.drop_column("notifications", "actor_id")
    if _has_column("orders", "approver_id"):
        op.drop_column("orders", "approver_id")
    if _has_column("vendors", "vendor_token_hash"):
        op.drop_index("idx_vendor_token_hash", table_name="vendors")
        op.drop_column("vendors", "vendor_token_hash")
    op.drop_index("idx_orders_deleted_at", table_name="orders")
    op.drop_index("idx_inventory_deleted_at", table_name="inventory_items")
