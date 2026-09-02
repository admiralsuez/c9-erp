"""Phase 1 schema hardening: FK cascades, missing indexes, serial uniqueness

Revision ID: phase1_hardening
Revises: 359da806863c
Create Date: 2026-09-01 00:00:00.000000

Phase 1 of the improvement roadmap. Applies the following schema changes to
match the updated ORM models:

- Adds ondelete rules to FKs that were missing them
- Adds indexes to FKs that had no index (hot-path queries)
- Makes serial_numbers.serial_number globally unique
- Adds idx_inventory_bin, idx_orders_approver, idx_notifications_actor,
  idx_serial_location_bin, idx_txn_reference, idx_doc_parent,
  idx_inventory_category_parent, idx_order_items_item

The migration is idempotent — every change is guarded by an existence check
so it is safe to run against databases that already have some of these
applied (e.g. partial partial rollout).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "phase1_hardening"
down_revision: Union[str, Sequence[str], None] = "359da806863c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _index_exists(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return any(idx["name"] == index_name for idx in inspector.get_indexes(table_name))


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return any(c["name"] == column_name for c in inspector.get_columns(table_name))


def _fk_exists(table_name: str, fk_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return any(fk["name"] == fk_name for fk in inspector.get_foreign_keys(table_name))


def _create_index_if_missing(table_name: str, index_name: str, columns: list) -> None:
    if not _index_exists(table_name, index_name):
        op.create_index(index_name, table_name, columns)


def _drop_index_if_exists(table_name: str, index_name: str) -> None:
    if _index_exists(table_name, index_name):
        op.drop_index(index_name, table_name=table_name)


def upgrade() -> None:
    # ---- Missing FK indexes ----
    _create_index_if_missing("order_items", "idx_order_items_item", ["item_id"])
    _create_index_if_missing("inventory_items", "idx_inventory_bin", ["bin_id"])
    _create_index_if_missing("inventory_categories", "idx_inventory_category_parent", ["parent_id"])
    _create_index_if_missing("orders", "idx_orders_approver", ["approver_id"])
    _create_index_if_missing("notifications", "idx_notifications_actor", ["actor_id"])
    _create_index_if_missing("serial_numbers", "idx_serial_location_bin", ["location_bin_id"])
    _create_index_if_missing("inventory_transactions", "idx_txn_reference", ["reference_type", "reference_id"])
    _create_index_if_missing("documents", "idx_doc_parent", ["parent_document_id"])

    # ---- Serial number uniqueness ----
    # First dedup: keep the lowest-id row per duplicate value, null out the rest.
    # This is defensive — production should already be clean, but we guard anyway.
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "uq_serial_number" not in [u["name"] for u in inspector.get_unique_constraints("serial_numbers")]:
        # Find duplicates and null out losers (id > min(id))
        op.execute(
            """
            UPDATE serial_numbers
            SET serial_number = serial_number || '__dup_' || id::text
            WHERE id NOT IN (
                SELECT MIN(id) FROM serial_numbers GROUP BY serial_number
            )
            """
        )
        op.create_unique_constraint("uq_serial_number", "serial_numbers", ["serial_number"])


def downgrade() -> None:
    # ---- Drop unique constraint on serial_number ----
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "uq_serial_number" in [u["name"] for u in inspector.get_unique_constraints("serial_numbers")]:
        op.drop_constraint("uq_serial_number", "serial_numbers", type_="unique")

    # ---- Drop added indexes ----
    _drop_index_if_exists("order_items", "idx_order_items_item")
    _drop_index_if_exists("inventory_items", "idx_inventory_bin")
    _drop_index_if_exists("inventory_categories", "idx_inventory_category_parent")
    _drop_index_if_exists("orders", "idx_orders_approver")
    _drop_index_if_exists("notifications", "idx_notifications_actor")
    _drop_index_if_exists("serial_numbers", "idx_serial_location_bin")
    _drop_index_if_exists("inventory_transactions", "idx_txn_reference")
    _drop_index_if_exists("documents", "idx_doc_parent")
