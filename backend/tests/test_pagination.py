"""
Phase 2.1 test suite: pagination edge cases for ``PaginatedResponse``.

Verifies:
  - ``pages`` is computed correctly for empty, partial, exact-multiple, and
    oversized page requests.
  - The factory ``.build()`` clamps the input to non-negative values.
  - The schema is generic and round-trips through Pydantic.
"""
import pytest
from pydantic import BaseModel

from app.schemas.common import PaginatedResponse


class _Row(BaseModel):
    id: int
    name: str


class TestPaginatedResponse:
    """Unit tests for ``PaginatedResponse`` envelope."""

    def test_pages_with_zero_items(self):
        body = PaginatedResponse[_Row].build(items=[], total=0, page=1, size=20)
        assert body.total == 0
        assert body.pages == 0
        assert body.items == []

    def test_pages_partial_last_page(self):
        # 25 items at size 10 -> 3 pages (10 + 10 + 5)
        body = PaginatedResponse[_Row].build(
            items=[_Row(id=i, name=f"r{i}") for i in range(10)],
            total=25, page=3, size=10,
        )
        assert body.pages == 3

    def test_pages_exact_multiple(self):
        # 30 items at size 10 -> exactly 3 pages
        body = PaginatedResponse[_Row].build(
            items=[_Row(id=i, name=f"r{i}") for i in range(10)],
            total=30, page=2, size=10,
        )
        assert body.pages == 3

    def test_pages_with_size_zero(self):
        # Edge case: size 0 must not divide-by-zero
        body = PaginatedResponse[_Row].build(items=[], total=5, page=1, size=0)
        assert body.pages == 0

    def test_pages_single_item(self):
        body = PaginatedResponse[_Row].build(
            items=[_Row(id=1, name="only")],
            total=1, page=1, size=20,
        )
        assert body.pages == 1

    def test_schema_round_trip(self):
        body = PaginatedResponse[_Row].build(
            items=[_Row(id=1, name="x")],
            total=1, page=1, size=20,
        )
        d = body.model_dump()
        assert set(d.keys()) == {"items", "total", "page", "size", "pages"}
        assert d["items"][0]["name"] == "x"
        assert d["pages"] == 1

    def test_pagination_helpers_consistency(self):
        """``PaginatedResponse.build`` agrees with the underlying helper formula."""
        from app.services.pagination_utils import total_pages as tp
        for total in (0, 1, 7, 25, 100, 101):
            for size in (1, 5, 10, 20):
                expected = tp(total, size) if total > 0 else 0
                body = PaginatedResponse[_Row].build(
                    items=[], total=total, page=1, size=size,
                )
                assert body.pages == expected, (
                    f"mismatch at total={total} size={size}: "
                    f"got {body.pages}, expected {expected}"
                )


class TestPaginationUtilsEdgeCases:
    """Property-style tests for the pagination helpers."""

    @pytest.mark.parametrize("page", [0, -1, -100])
    def test_normalize_page_clamps_to_one(self, page):
        from app.services.pagination_utils import normalize_page_size
        p, _ = normalize_page_size(page, 20)
        assert p == 1

    @pytest.mark.parametrize("size", [0, -5, 1000, 99999])
    def test_normalize_size_clamps(self, size):
        from app.services.pagination_utils import normalize_page_size
        _, s = normalize_page_size(1, size)
        # Clamped to [1, 100]
        assert 1 <= s <= 100

    def test_normalize_handles_none(self):
        from app.services.pagination_utils import normalize_page_size
        p, s = normalize_page_size(None, None)
        assert p == 1
        assert s == 20

    def test_normalize_handles_garbage(self):
        from app.services.pagination_utils import normalize_page_size
        p, s = normalize_page_size("garbage", "more garbage")
        assert p == 1
        assert s == 20
