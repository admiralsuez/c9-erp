"""add vendor pincode column

Revision ID: e7f8g9h0i1j2
Revises: a1b2c3d4e5f6
Create Date: 2026-07-16 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e7f8g9h0i1j2"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = [c["name"] for c in inspector.get_columns(table)]
    return column in cols


def upgrade() -> None:
    if not _has_column("vendors", "pincode"):
        op.add_column(
            "vendors",
            sa.Column("pincode", sa.String(10), nullable=True)
        )


def downgrade() -> None:
    op.drop_column("vendors", "pincode")
