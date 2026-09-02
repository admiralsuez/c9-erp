"""Phase 1.3: Vendor type denormalization backfill and index

Revision ID: phase1_vendor_type_sync
Revises: phase1_hardening
Create Date: 2026-09-01 00:00:00.000000

Phase 1.3 of the improvement roadmap. The ``vendors`` table has two columns
holding the same business fact:
  - ``vendor_type`` (String, legacy)
  - ``vendor_type_id`` (FK to vendor_types.id, authoritative)

This migration:
  1. Adds ``idx_vendor_type_id`` for fast joins and FK lookups.
  2. Backfills ``vendor_type_id`` from ``vendor_type`` where the FK is null
     but a matching vendor_type row exists. This ensures existing data is
     consistent with the FK-first reads.
  3. Syncs ``vendor_type`` strings to match the FK for vendors that have
     a non-null FK but a stale string (defensive).
  4. Marks the legacy ``vendor_type`` column for removal in a future
     migration once application code has been migrated off it.

Note: removing the column entirely is a Phase 2 task because the column
is still referenced by the vendor list filter (``Vendor.vendor_type == vendor_type``).
Switching that filter to a JOIN on vendor_types is non-trivial and
out of scope here.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "phase1_vendor_type_sync"
down_revision: Union[str, Sequence[str], None] = "phase1_hardening"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    indexes = [idx["name"] for idx in inspector.get_indexes("vendors")]

    # ---- 1. Add the FK index ----
    if "idx_vendor_type_id" not in indexes:
        op.create_index("idx_vendor_type_id", "vendors", ["vendor_type_id"])

    # ---- 2. Backfill vendor_type_id from vendor_type string ----
    # Only matches vendors where the FK is currently null but a matching
    # vendor_types row exists. Idempotent.
    op.execute(
        """
        UPDATE vendors v
        SET vendor_type_id = vt.id
        FROM vendor_types vt
        WHERE v.vendor_type_id IS NULL
          AND LOWER(TRIM(v.vendor_type)) = LOWER(vt.name)
        """
    )

    # ---- 3. Sync vendor_type string from the FK (defensive) ----
    op.execute(
        """
        UPDATE vendors v
        SET vendor_type = vt.name
        FROM vendor_types vt
        WHERE v.vendor_type_id = vt.id
          AND v.vendor_type IS DISTINCT FROM vt.name
        """
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    indexes = [idx["name"] for idx in inspector.get_indexes("vendors")]

    if "idx_vendor_type_id" in indexes:
        op.drop_index("idx_vendor_type_id", table_name="vendors")
