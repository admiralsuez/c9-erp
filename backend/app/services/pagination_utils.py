"""Pagination helpers.

Offset/limit computation, query slicing, and sort-key normalization shared by
list endpoints across routers.
"""
from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple

from sqlalchemy import asc, desc
from sqlalchemy.orm import Query


DEFAULT_PAGE = 1
DEFAULT_SIZE = 20
MAX_SIZE = 100


def normalize_page_size(page: Optional[int], size: Optional[int]) -> Tuple[int, int]:
    """Clamp page/size into valid ranges.

    Args:
        page: Requested page (1-based). Invalid/None -> 1.
        size: Requested page size. Invalid/None -> DEFAULT_SIZE; capped at MAX_SIZE.

    Returns:
        ``(page, size)`` tuple ready for offset/limit.
    """
    try:
        page = int(page or DEFAULT_PAGE)
    except (TypeError, ValueError):
        page = DEFAULT_PAGE
    if page < 1:
        page = 1

    try:
        size = int(size or DEFAULT_SIZE)
    except (TypeError, ValueError):
        size = DEFAULT_SIZE
    size = max(1, min(size, MAX_SIZE))

    return page, size


def get_offset(page: int, size: int) -> int:
    """Compute the SQL offset for a (1-based) page."""
    return (page - 1) * size


def total_pages(total: int, size: int) -> int:
    """Compute the number of pages for a total count."""
    if size <= 0:
        return 0
    return (total + size - 1) // size


def paginate_query(
    query: Query,
    page: Optional[int] = None,
    size: Optional[int] = None,
    default_size: int = DEFAULT_SIZE,
) -> Tuple[Query, int, int, int]:
    """Slice a SQLAlchemy query with pagination.

    Args:
        query: The base query (counted on ``query.count()``).
        page: Requested page.
        size: Requested page size.
        default_size: Fallback size when none supplied.

    Returns:
        ``(sliced_query, page, size, total)`` — caller fetches ``.all()`` on
        the sliced query and computes ``total_pages`` if needed.
    """
    page, size = normalize_page_size(page, size)
    size = size if size is not None else default_size
    total = query.count()
    sliced = query.offset(get_offset(page, size)).limit(size)
    return sliced, page, size, total


def make_sort_clause(sort: Optional[str], order: Optional[str], column_map: Dict[str, Any]) -> Any:
    """Build a SQLAlchemy order-by expression from a (sort, order) pair.

    Args:
        sort: Sort key; looked up in ``column_map``. Unknown keys are ignored.
        order: ``asc`` or ``desc`` (case-insensitive). Defaults to ``asc``.
        column_map: Mapping of public sort keys to SQLAlchemy columns.

    Returns:
        A column/expression with ``.asc()``/``.desc()`` applied, or ``None``.
    """
    column = column_map.get(sort or "")
    if column is None:
        return None
    if (order or "").lower() == "desc":
        return desc(column)
    return asc(column)


def apply_sort(
    query: Query,
    sort: Optional[str],
    order: Optional[str],
    column_map: Dict[str, Any],
    fallback: Optional[Any] = None,
) -> Query:
    """Apply an optional sort to a query with a fallback order-by."""
    clause = make_sort_clause(sort, order, column_map)
    if clause is not None:
        return query.order_by(clause)
    if fallback is not None:
        return query.order_by(fallback)
    return query
