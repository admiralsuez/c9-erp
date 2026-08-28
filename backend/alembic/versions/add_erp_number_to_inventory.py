"""Add erp_number column to inventory_items

Revision ID: add_erp_number_to_inventory
Revises: orders_challan_order_date
Create Date: 2026-08-28 00:00:00.000000

Adds the inventory_items.erp_number column (String(100), unique, nullable)
introduced by the ERP number feature.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_erp_number_to_inventory'
down_revision: Union[str, Sequence[str], None] = 'orders_challan_order_date'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = [c["name"] for c in inspector.get_columns("inventory_items")]

    if "erp_number" not in cols:
        op.add_column("inventory_items", sa.Column("erp_number", sa.String(100), nullable=True, unique=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = [c["name"] for c in inspector.get_columns("inventory_items")]

    if "erp_number" in cols:
        op.drop_column("inventory_items", "erp_number")
