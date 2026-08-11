"""
Phase 1 - Standardized error response format tests.

Every error response must follow the standard shape:
status, message, error_code, details, timestamp, path (plus legacy `detail`).
"""

import pytest
from app.core.error_handler import (
    ErrorResponse,
    ERROR_CODE_CATALOG,
    build_error_response,
)


def assert_standard_error(body, expected_code=None, expected_status=None):
    """Validate the standardized error body shape."""
    assert body["status"] == "error"
    assert isinstance(body["message"], str) and body["message"]
    assert body["error_code"] in set(ERROR_CODE_CATALOG.values()) | {"INTERNAL_ERROR"}
    assert "timestamp" in body and body["timestamp"]
    assert "path" in body and isinstance(body["path"], str)
    # Legacy alias must match message for frontend compatibility
    assert body["detail"] == body["message"]
    if expected_code:
        assert body["error_code"] == expected_code
    if expected_status:
        assert body["status"] == expected_status


class TestErrorSchema:
    def test_error_response_model(self):
        body = ErrorResponse(
            message="Not found",
            error_code="NOT_FOUND",
            timestamp="2026-08-11T00:00:00Z",
            path="/api/orders/999",
            detail="Not found",
        )
        assert body.status == "error"
        assert body.detail == body.message

    def test_build_error_response_http_exception(self):
        from starlette.requests import Request

        scope = {
            "type": "http",
            "method": "GET",
            "scheme": "http",
            "path": "/api/orders/999",
            "raw_path": b"/api/orders/999",
            "query_string": b"",
            "root_path": "",
            "headers": [],
            "server": ("test", 80),
            "client": ("1.2.3.4", 1234),
        }
        body = build_error_response(Request(scope), 404, "Order not found")
        assert_standard_error(body, expected_code="NOT_FOUND")


class TestHTTPErrorFormatting:
    def test_404_standard_format(self, client):
        response = client.get("/api/nonexistent-endpoint")
        assert response.status_code == 404
        assert_standard_error(response.json(), expected_code="NOT_FOUND")

    def test_401_standard_format(self, client):
        response = client.post("/auth/login", json={
            "email": "noone@test.com",
            "password": "wrong",
        })
        # Could be 401 (invalid creds) or 429 (rate limited) - both standard
        body = response.json()
        assert_standard_error(body)
        assert response.status_code in (401, 429)

    def test_validation_error_standard_format(self, client):
        # Missing required fields -> 422
        response = client.post("/auth/login", json={})
        assert response.status_code == 422
        body = response.json()
        assert_standard_error(body, expected_code="VALIDATION_ERROR")
        assert body["details"] is not None

    def test_conflict_standard_format(self, client, db_session):
        """Business-rule conflict (duplicate vendor) uses standard format."""
        from tests.conftest import (
            create_test_roles_and_perms,
            create_test_user,
            create_test_vendor,
            login_as,
        )

        admin_role, _, _, _ = create_test_roles_and_perms(db_session)
        create_test_user(db_session, "admin@test.com", "password", admin_role)
        create_test_vendor(db_session, name="Acme Supplies")

        headers = login_as(client, "admin@test.com", "password")
        response = client.post(
            "/vendors",
            json={
                "name": "Acme Supplies",
                "email": "dup@test.com",
                "phone": "9999999999",
            },
            headers=headers,
        )
        assert response.status_code == 409
        body = response.json()
        assert_standard_error(body, expected_code="CONFLICT")

    def test_unknown_error_code_maps_to_internal(self, client):
        from starlette.requests import Request

        scope = {
            "type": "http",
            "method": "GET",
            "scheme": "http",
            "path": "/x",
            "raw_path": b"/x",
            "query_string": b"",
            "root_path": "",
            "headers": [],
            "server": ("test", 80),
            "client": ("1.2.3.4", 1),
        }
        body = build_error_response(Request(scope), 599, "weird")
        assert body["error_code"] == "INTERNAL_ERROR"


class TestRateLimitErrorFormat:
    def test_429_standard_format(self, client, db_session):
        from tests.conftest import create_test_roles_and_perms, create_test_user
        from app.core.config import settings

        admin_role, _, _, _ = create_test_roles_and_perms(db_session)
        create_test_user(db_session, "admin@test.com", "password", admin_role)

        for _ in range(settings.RATE_LIMIT_LOGIN_LIMIT):
            client.post("/auth/login", json={
                "email": "admin@test.com",
                "password": "wrong-password",
            })

        response = client.post("/auth/login", json={
            "email": "admin@test.com",
            "password": "wrong-password",
        })
        assert response.status_code == 429
        body = response.json()
        assert_standard_error(body, expected_code="RATE_LIMITED")
        assert "Retry-After" in response.headers
