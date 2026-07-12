"""create_full_schema

Ensures all application tables exist. Replaces the previous
Base.metadata.create_all() call in main.py with a proper migration.
Uses SQLAlchemy's create_all under the hood — idempotent on existing tables.

Revision ID: abb4ff9cf8d5
Revises: 5310d2cc89ed
Create Date: 2026-07-13 18:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
from app.core.database import Base

revision: str = "abb4ff9cf8d5"
down_revision: Union[str, Sequence[str], None] = "5310d2cc89ed"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
