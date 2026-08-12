"""Response and error formatting utilities.

Helpers for producing consistent success/error response shapes and for
formatting common values (dates, numbers) across the API.
"""
from __future__ import annotations
from datetime import datetime, date
from decimal import Decimal
from typing import Any, Dict, List, Optional
import time


def format_iso(dt: Optional[datetime]) -> Optional[str]:
    """Format a datetime as ISO-8601 string (or None)."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.now().astimezone().tzinfo)
    return dt.isoformat()


def format_date_iso(d: Optional[date]) -> Optional[str]:
    """Format a date as ISO-8601 string (or None)."""
    return d.isoformat() if d is not None else None


def format_number(value: Any, places: int = 2) -> Optional[float]:
    """Round a numeric value to ``places`` decimals (None passes through)."""
    if value is None:
        return None
    try:
        return round(float(value), places)
    except (TypeError, ValueError):
        return value


def format_money(value: Any) -> str:
    """Format a number as a 2-decimal money string."""
    try:
        return f"{Decimal(str(value)):.2f}"
    except Exception:
        return "0.00"


def success_response(
    data: Any = None,
    message: str = "Success",
    meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Standard success body: ``{status, message, data, meta}``."""
    return {
        "status": "success",
        "message": message,
        "data": data,
        "meta": meta or {},
    }


def error_response(
    message: str,
    error_code: str = "INTERNAL_ERROR",
    details: Any = None,
    path: str = "",
    status_code: int = 500,
    timestamp: Optional[str] = None,
) -> Dict[str, Any]:
    """Standard error body compatible with app.core.error_handler.

    Mirrors the shape produced by the global exception handlers so route-level
    fallbacks stay consistent: ``{status, message, error_code, details,
    timestamp, path, detail}``.
    """
    stamp = timestamp or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return {
        "status": "error",
        "message": message,
        "error_code": error_code,
        "details": details,
        "timestamp": stamp,
        "path": path,
        "detail": message,
    }


def paginated(
    items: List[Any],
    total: int,
    page: int,
    size: int,
) -> Dict[str, Any]:
    """Build the standard paginated envelope used across list endpoints."""
    total_pages = (total + size - 1) // size if size > 0 else 0
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "total_pages": total_pages,
    }
