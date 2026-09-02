"""Reusable SQLAlchemy mixins.

Mixins that bundle the columns shared by every model — timestamps, soft
delete, and audit fields. Importing and inheriting these keeps models
declarative and ensures consistent behavior across the schema.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Column, DateTime
from sqlalchemy.sql import func


class TimestampMixin:
    """Adds ``created_at`` and ``updated_at`` columns populated by Postgres
    so application code never has to set them explicitly.

    Both columns are ``NOT NULL`` and default to ``func.now()``. ``updated_at``
    is auto-bumped on every UPDATE.
    """
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SoftDeleteMixin:
    """Adds a ``deleted_at`` column for tombstone-style soft deletes.

    Soft-deleted rows are filtered out by the convention
    ``cls.deleted_at == None`` at query time. A helper ``soft_delete``
    stamps ``deleted_at`` to the current UTC time.
    """
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)

    def soft_delete(self) -> None:
        """Mark this instance as deleted without touching the DB."""
        self.deleted_at = datetime.now(timezone.utc)


class FullAuditMixin(TimestampMixin, SoftDeleteMixin):
    """Bundle the common ``created_at`` / ``updated_at`` / ``deleted_at`` set.

    Use this for entities that participate in soft delete (most user-facing
    models). Entities that don't need soft delete should inherit
    :class:`TimestampMixin` directly.
    """
    pass


__all__ = [
    "TimestampMixin",
    "SoftDeleteMixin",
    "FullAuditMixin",
]
