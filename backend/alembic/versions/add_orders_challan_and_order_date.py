"""Add challan_book_number and order_date to orders

Revision ID: add_orders_challan_and_order_date
Revises: fix_duplicate_columns
Create Date: 2026-08-19 00:00:00.000000

Adds the orders columns introduced by the Phase 1/2 order features that were
never covered by a migration:
- orders.challan_book_number (String(100))  # challan book number when dispatching
- orders.order_date (DateTime(timezone=True))  # optional backdate for order
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'orders_challan_order_date'
down_revision: Union[str, Sequence[str], None] = 'fix_duplicate_columns'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = [c["name"] for c in inspector.get_columns("orders")]

    if "challan_book_number" not in cols:
        op.add_column("orders", sa.Column("challan_book_number", sa.String(100), nullable=True))
    if "order_date" not in cols:
        op.add_column("orders", sa.Column("order_date", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = [c["name"] for c in inspector.get_columns("orders")]

    if "order_date" in cols:
        op.drop_column("orders", "order_date")
    if "challan_book_number" in cols:
        op.drop_column("orders", "challan_book_number")