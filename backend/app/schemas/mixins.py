"""Reusable Pydantic schema mixins.

Use these to keep response/request schemas consistent across the API.
Inherit ``TimestampResponse`` on any entity that exposes ``created_at`` /
``updated_at`` and ``SoftDeleteResponse`` on entities that participate in
soft delete.
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TimestampResponse(BaseModel):
    """Standard ``created_at`` / ``updated_at`` exposure for response models."""
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IdentifierResponse(BaseModel):
    """Standard ``id`` exposure so list responses carry the primary key."""
    id: int = Field(..., description="Primary key")


class SoftDeleteResponse(BaseModel):
    """Expose ``deleted_at`` to clients that want to filter archived rows
    explicitly (e.g. admin tooling)."""
    deleted_at: Optional[datetime] = None


__all__ = [
    "TimestampResponse",
    "IdentifierResponse",
    "SoftDeleteResponse",
]
