"""
Phase 1 - Rate limiting tests.

Covers the shared RateLimiter service and HTTP-level enforcement
(login attempts, global per-IP/per-user middleware, rate-limit headers).
"""

import pytest
from app.services.rate_limiter import (
    RateLimiter,
    RateLimitMiddleware,
    RateLimitExceeded,
    rate_limiter,
)
from app.core.config import settings


class TestRateLimiterUnit:
    """Unit tests for the sliding-window RateLimiter."""

    def test_allows_within_limit(self):
        limiter = RateLimiter()
        key = "ip:test"

        for _ in range(5):
            allowed, retry_after = limiter.check(key, limit=5, window=60)
            assert allowed is True
            assert retry_after == 0

    def test_rejects_over_limit(self):
        limiter = RateLimiter()
        key = "ip:test"

        for _ in range(5):
            limiter.check(key, limit=5, window=60)

        allowed, retry_after = limiter.check(key, limit=5, window=60)
        assert allowed is False
        assert retry_after > 0

    def test_independent_keys(self):
        limiter = RateLimiter()
        limiter.check("ip:a", limit=1, window=60)
        allowed, _ = limiter.check("ip:b", limit=1, window=60)
        assert allowed is True

    def test_window_resets_after_expiry(self, monkeypatch):
        limiter = RateLimiter()
        key = "ip:test"
        import time

        monkeypatch.setattr(time, "time", lambda: 1000.0)
        limiter.check(key, limit=1, window=10)
        allowed, _ = limiter.check(key, limit=1, window=10)
        assert allowed is False

        monkeypatch.setattr(time, "time", lambda: 1011.0)
        allowed, _ = limiter.check(key, limit=1, window=10)
        assert allowed is True

    def test_reset_clears_all(self):
        limiter = RateLimiter()
        limiter.check("ip:a", limit=1, window=60)
        limiter.check("ip:b", limit=1, window=60)
        limiter.reset()
        assert limiter.size == 0

    def test_reset_single_key(self):
        limiter = RateLimiter()
        limiter.check("ip:a", limit=1, window=60)
        limiter.check("ip:b", limit=1, window=60)
        limiter.reset("ip:a")
        assert limiter.size == 1

    def test_rate_limit_exceeded_carries_metadata(self):
        exc = RateLimitExceeded(limit=5, retry_after=42, scope="login")
        assert exc.limit == 5
        assert exc.retry_after == 42
        assert exc.scope == "login"


class TestLoginRateLimit:
    """Login attempts are limited per IP (configurable)."""

    def test_login_blocked_after_limit(self, client, db_session):
        from tests.conftest import create_test_user, create_test_roles_and_perms

        admin_role, _, _, _ = create_test_roles_and_perms(db_session)
        create_test_user(db_session, "admin@test.com", "password", admin_role)

        limit = settings.RATE_LIMIT_LOGIN_LIMIT

        # First `limit` attempts with wrong password should be 401
        for _ in range(limit):
            response = client.post("/auth/login", json={
                "email": "admin@test.com",
                "password": "wrong-password",
            })
            assert response.status_code == 401

        # Next attempt should be rate-limited (429)
        response = client.post("/auth/login", json={
            "email": "admin@test.com",
            "password": "wrong-password",
        })
        assert response.status_code == 429
        assert response.json()["error_code"] == "RATE_LIMITED"

    def test_rate_limit_headers_present(self, client):
        response = client.get("/health")
        # /health is exempt; use an actual endpoint instead
        response = client.get("/docs")
        assert response.status_code in (200, 307)
        # hits are not rate limited for exempt paths, but a normal path should
        # still succeed and carry headers
        response = client.post("/auth/login", json={
            "email": "nobody@test.com",
            "password": "password",
        })
        assert response.status_code in (401, 429)
        if response.status_code == 401:
            assert "X-RateLimit-Limit" in response.headers
            assert "X-RateLimit-Remaining" in response.headers


class TestMiddlewareEnforcement:
    """Global middleware limits per-IP for anonymous requests."""

    def test_anonymous_public_limit(self, client, db_session):
        from tests.conftest import create_test_roles_and_perms, create_test_user
        admin_role, _, _, _ = create_test_roles_and_perms(db_session)
        create_test_user(db_session, "admin@test.com", "password", admin_role)

        limit = settings.RATE_LIMIT_PUBLIC_LIMIT
        # Hammer a public (unauthenticated) endpoint without hitting login's
        # stricter per-IP rule. Login is limited separately, so use /docs
        # bypass + an unauthenticated API endpoint that 401s but still counts.
        statuses = []
        for _ in range(min(limit + 2, 510)):
            r = client.get("/auth/me")
            statuses.append(r.status_code)
            if r.status_code == 429:
                break

        assert 429 in statuses
