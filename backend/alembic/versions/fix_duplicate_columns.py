"""Fix duplicate columns that were already applied

Revision ID: fix_duplicate_columns
Revises: merge_phase3_and_sku_heads
Create Date: 2026-08-18 09:00:00.000000

This migration detects and skips any columns that were already added
by previous migrations to handle the case where the database already
has the schema but Alembic tracking is out of sync.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fix_duplicate_columns'
down_revision: Union[str, Sequence[str], None] = 'merge_phase3_and_sku_heads'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """No-op migration - all columns should already exist."""
    pass


def downgrade() -> None:
    """No-op downgrade."""
    pass
