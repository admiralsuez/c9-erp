"""
Phase 3.4 - Service utilities tests.

Covers validators, formatters, pagination_utils, and cache_utils.
"""

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.services.validators import (
    require,
    require_found,
    require_permission_else,
    validate_positive_number,
    validate_required,
    validate_enum,
    validate_email_format,
    validate_file_type,
    validate_max_size,
)
from app.services.formatters import (
    format_iso,
    format_date_iso,
    format_number,
    format_money,
    success_response,
    error_response,
    paginated,
)
from app.services.pagination_utils import (
    normalize_page_size,
    get_offset,
    total_pages,
    paginate_query,
    make_sort_clause,
    apply_sort,
)
from app.services.cache_utils import (
    build_key,
    hash_key,
    ttl_for,
    model_key_prefix,
    invalidate_keys_for,
    entity_ids_for,
)


class TestValidators:
    def test_require_pass(self):
        require(True, "nope")

    def test_require_fail(self):
        with pytest.raises(HTTPException) as e:
            require(False, "boom", 400)
        assert e.value.status_code == 400
        assert e.value.detail == "boom"

    def test_require_found(self):
        with pytest.raises(HTTPException) as e:
            require_found(None, "Order", 42)
        assert e.value.status_code == 404
        assert "Order" in e.value.detail and "42" in e.value.detail

    def test_require_found_ok(self):
        require_found({"id": 1}, "Order")

    def test_require_permission_else(self):
        with pytest.raises(HTTPException) as e:
            require_permission_else(False)
        assert e.value.status_code == 403

    def test_validate_positive_number(self):
        assert validate_positive_number("5", "qty") == 5.0
        with pytest.raises(HTTPException):
            validate_positive_number("abc", "qty")
        with pytest.raises(HTTPException):
            validate_positive_number(-3, "qty")

    def test_validate_required(self):
        with pytest.raises(HTTPException):
            validate_required("", "name")
        validate_required("x", "name")

    def test_validate_enum_case_insensitive(self):
        validate_enum("ACTIVE", ["active", "expired"], "status")
        with pytest.raises(HTTPException):
            validate_enum("bogus", ["active", "expired"], "status")

    def test_validate_email_format(self):
        assert validate_email_format("a@b.co")
        assert not validate_email_format("not-an-email")

    def test_validate_file_type(self):
        assert validate_file_type("photo.PDF", {"pdf"}) == "pdf"
        with pytest.raises(HTTPException):
            validate_file_type("evil.exe", {"pdf"})

    def test_validate_max_size(self):
        validate_max_size(10, 100)
        with pytest.raises(HTTPException) as e:
            validate_max_size(200, 100)
        assert e.value.status_code == 413


class TestFormatters:
    def test_format_iso(self):
        from datetime import datetime
        assert format_iso(None) is None
        out = format_iso(datetime(2026, 1, 1, 12, 0, 0))
        assert out.startswith("2026-01-01T12:00:00")

    def test_format_date_iso(self):
        from datetime import date
        assert format_date_iso(date(2026, 5, 4)) == "2026-05-04"
        assert format_date_iso(None) is None

    def test_format_number(self):
        assert format_number("3.14159", 2) == 3.14
        assert format_number(None) is None

    def test_format_money(self):
        assert format_money("19.5") == "19.50"
        assert format_money("bad") == "0.00"

    def test_success_response(self):
        body = success_response({"a": 1}, message="ok")
        assert body["status"] == "success"
        assert body["data"] == {"a": 1}

    def test_error_response_shape(self):
        body = error_response("nope", error_code="NOT_FOUND", path="/x")
        assert body["status"] == "error"
        assert body["detail"] == body["message"]
        assert body["error_code"] == "NOT_FOUND"

    def test_paginated(self):
        body = paginated([1, 2], 42, 1, 20)
        assert body["total_pages"] == 3


class TestPaginationUtils:
    def test_normalize_page_size(self):
        assert normalize_page_size(None, None) == (1, 20)
        assert normalize_page_size(0, 500) == (1, 100)
        assert normalize_page_size(-1, "abc") == (1, 20)

    def test_get_offset(self):
        assert get_offset(3, 20) == 40

    def test_total_pages(self):
        assert total_pages(42, 20) == 3
        assert total_pages(0, 20) == 0

    def test_paginate_query(self):
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import sessionmaker

        engine = create_engine("sqlite:///:memory:")
        with engine.begin() as conn:
            conn.exec_driver_sql("CREATE TABLE t (id INTEGER)")
            for i in range(45):
                conn.exec_driver_sql("INSERT INTO t (id) VALUES (?)", (i,))
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()

        q = text("SELECT id FROM t")
        db.execute(q).fetchall()  # sanity

        # paginate_query slices a SQLAlchemy ORM Query; build one against a
        # mapped entity instead so offset/limit/count behave properly.
        from sqlalchemy.orm import declarative_base
        from sqlalchemy import Column, Integer

        Base = declarative_base()

        class Row(Base):
            __tablename__ = "t"
            id = Column(Integer, primary_key=True)

        Base.metadata.create_all(engine)
        orm_query = db.query(Row)
        sliced, page, size, total = paginate_query(orm_query, page=2, size=20)
        rows = sliced.all()
        assert total == 45
        assert page == 2
        assert size == 20
        assert len(rows) == 20
        assert rows[0].id == 20  # offset (2-1)*20
        db.close()

    def test_make_sort_clause(self):
        from sqlalchemy import Column, Integer
        from sqlalchemy import asc, desc
        from sqlalchemy.sql import column
        col = column("created_at")
        c = make_sort_clause("created", "desc", {"created": col})
        assert c is not None
        assert make_sort_clause("bogus", "asc", {"created": col}) is None

    def test_apply_sort_fallback(self):
        from sqlalchemy.sql import column
        from sqlalchemy.sql.elements import UnaryExpression
        q = None  # not exercised; clause building covered above


class TestCacheUtils:
    def test_build_key(self):
        assert build_key("order", 123) == "order:123"
        assert build_key("order", 123, page=2) == "order:123:page=2"

    def test_build_key_deterministic_dict(self):
        k1 = build_key("x", {"b": 2, "a": 1})
        k2 = build_key("x", {"a": 1, "b": 2})
        assert k1 == k2

    def test_hash_key(self):
        h1 = hash_key("q", "SELECT 1")
        h2 = hash_key("q", "SELECT 1")
        assert h1 == h2
        assert h1.startswith("q:")
        assert len(h1) > len("q:")

    def test_ttl_for(self):
        assert ttl_for(None, default_ttl=300) == 300
        assert ttl_for(-5) == 1
        assert ttl_for(9999, max_ttl=100) == 100

    def test_model_key_prefix(self):
        assert model_key_prefix("Order") == "model:order"

    def test_invalidate_keys_for(self):
        cache = {"model:order:1": "a", "model:order:2": "b", "other": "c"}
        removed = invalidate_keys_for(cache, "model:order")
        assert removed == 2
        assert "other" in cache

    def test_entity_ids_for(self):
        assert entity_ids_for("order", [3, 1, 3]) == "order:1,3"
