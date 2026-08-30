"""Add is_approved field to notifications

Revision ID: 359da806863c
Revises: add_erp_number_to_inventory
Create Date: 2026-08-30 19:10:22.121096

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '359da806863c'
down_revision: Union[str, Sequence[str], None] = 'add_erp_number_to_inventory'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add is_approved column
    op.add_column('notifications', sa.Column('is_approved', sa.Boolean(), nullable=False, server_default='false'))
    
    # Add index for approval notifications query
    op.create_index('idx_notifications_approval', 'notifications', ['user_id', 'type', 'is_approved'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop index
    op.drop_index('idx_notifications_approval', table_name='notifications')
    
    # Drop column
    op.drop_column('notifications', 'is_approved')
