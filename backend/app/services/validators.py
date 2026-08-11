"""Centralized validation utilities.

Reusable validators for common business rules used across routers and
services. Each validator raises ``HTTPException`` (or returns a value)
so callers can rely on consistent error behavior.
"""
from __future__ import annotations
from typing import Any, Optional
import re

from fastapi import HTTPException, status


def require(condition: bool, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> None:
    """Raise an HTTP 4xx error unless ``condition`` is truthy.

    Thin convenience wrapper around ``HTTPException`` so callers read as
    declarative checks::

        require(item is not None, "Item not found", status.HTTP_404_NOT_FOUND)
    """
    if not condition:
        raise HTTPException(status_code=status_code, detail=detail)


def require_found(entity: Any, name: str = "Record", id_value: Optional[Any] = None) -> None:
    """Raise 404 when an entity lookup returned ``None``.

    Args:
        entity: The fetched object (None means not found).
        name: Human-readable entity name for the error message.
        id_value: Optional identifier shown in the message.
    """
    if entity is None:
        suffix = f" {id_value}" if id_value is not None else ""
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{name}{suffix} not found",
        )


def require_permission_else(has: bool, detail: str = "Insufficient permissions") -> None:
    """Raise 403 unless the caller holds the required permission."""
    if not has:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def validate_positive_number(value: Any, field_name: str) -> float:
    """Coerce and validate that a value is a positive number.

    Returns:
        The coerced float.

    Raises:
        HTTPException 400: value is not numeric or is < 0.
    """
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} must be a number",
        )
    if number < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} must be zero or greater",
        )
    return number


def validate_required(value: Any, field_name: str) -> None:
    """Raise 400 when a required field is missing or empty."""
    if value is None or (isinstance(value, str) and not value.strip()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} is required",
        )


def validate_enum(value: Any, allowed: Any, field_name: str, case_sensitive: bool = False) -> None:
    """Raise 400 when ``value`` is not one of ``allowed``.

    Args:
        value: The value to check (string or enum member).
        allowed: Iterable of allowed values.
        field_name: Field name for the error message.
        case_sensitive: When False, string values are compared case-insensitively.
    """
    compare = value if case_sensitive else str(value).lower()
    allowed_compare = [
        str(a).lower() if not case_sensitive else str(a)
        for a in allowed
    ]
    if compare not in allowed_compare:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} must be one of: {', '.join(sorted(set(allowed_compare)))}",
        )


def validate_email_format(email: str) -> bool:
    """Lightweight email shape check (no DNS resolution).

    Returns:
        True when the string looks like ``x@y.z``.
    """
    pattern = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    return bool(pattern.match(email or ""))


def validate_file_type(filename: str, allowed_types: Any, field_name: str = "File type") -> str:
    """Validate a filename's extension against an allow-list.

    Args:
        filename: Uploaded filename.
        allowed_types: Iterable of allowed extensions (lowercase, no dot).
        field_name: Label used in the error message.

    Returns:
        The validated lowercase extension.
    """
    ext = filename.rsplit(".", 1)[1].lower() if "." in filename else ""
    if ext not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} .{ext or '(none)'} not allowed. Allowed: {', '.join(sorted(allowed_types))}",
        )
    return ext


def validate_max_size(size: int, max_size: int, field_name: str = "File") -> None:
    """Raise 413 when ``size`` exceeds ``max_size`` (bytes)."""
    if size > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"{field_name} too large. Maximum size: {max_size / 1024 / 1024:.1f}MB",
        )
