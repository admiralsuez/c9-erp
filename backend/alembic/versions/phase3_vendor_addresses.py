"""Phase 3: Add parent_id to vendors for vendor address hierarchy.

Adds:
- vendors.parent_id (self-referencing FK for vendor addresses)
- idx_vendor_parent index for performance
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "phase3_vendor_addresses"
down_revision: Union[str, Sequence[str], None] = "18e7191c4a73"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = [c["name"] for c in inspector.get_columns("vendors")]

    if "parent_id" not in cols:
        op.add_column("vendors",
            sa.Column("parent_id", sa.Integer(), sa.ForeignKey("vendors.id"), nullable=True))
        op.create_index("idx_vendor_parent", "vendors", ["parent_id"])


def downgrade() -> None:
    op.drop_index("idx_vendor_parent", table_name="vendors")
    op.drop_column("vendors", "parent_id")
