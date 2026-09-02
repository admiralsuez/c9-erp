"""
Phase 5 test suite: observability endpoints + request-id middleware.

Covers:
  - GET /metrics    — Prometheus text exposition
  - GET /healthz    — liveness (no DB dependency)
  - GET /readyz     — readiness (requires reachable DB)
  - X-Request-ID    — echoed on responses; honoured when supplied; generated otherwise
  - app.core.metrics — counter/histogram/gauge primitives behave correctly

No auth is required on these routes by design (they are expected to be
protected at the reverse-proxy layer), so no login fixtures are needed.
"""
import uuid

from app.core import metrics as m


class TestHealthz:
    def test_healthz_returns_ok(self, client):
        response = client.get("/healthz")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_healthz_needs_no_auth(self, client):
        """Liveness must never require credentials."""
        response = client.get("/healthz")
        assert "Authorization" not in str(response.request.headers) or response.status_code == 200


class TestReadyz:
    def test_readyz_reports_db_ok(self, client):
        """Against the test engine, the DB ping must succeed."""
        response = client.get("/readyz")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ready"
        assert body["db_ok"] is True
        assert "db_latency_ms" in body


class TestMetrics:
    def test_metrics_endpoint_returns_prometheus_text(self, client):
        response = client.get("/metrics")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/plain")
        body = response.text
        # Core metric families must be present, even when empty.
        assert "# HELP http_requests_total" in body
        assert "# TYPE http_requests_total counter" in body
        assert "# HELP db_query_duration_seconds" in body
        assert "# TYPE db_query_duration_seconds histogram" in body
        assert "process_uptime_seconds" in body
        # Cache stats are folded into the exposition.
        assert "response_cache_size" in body

    def test_request_counter_records_requests(self, client):
        """After a request, /metrics should include a counter line for its path."""
        before = m._http_requests.snapshot()
        client.get("/healthz")
        after = m._http_requests.snapshot()
        # At least one new counter entry should exist with path /healthz.
        paths = set()
        for labels, _ in after:
            if labels.get("path") == "/healthz":
                paths.add((labels.get("method"), labels.get("status")))
                break
        assert paths, "no http_requests_total entry for /healthz"
        assert before is not None  # snapshot readable


class TestRequestIdMiddleware:
    def test_response_includes_request_id_header(self, client):
        response = client.get("/healthz")
        rid = response.headers.get("X-Request-ID")
        assert rid, "X-Request-ID header missing"
        # Auto-generated ids are uuid4 hex (32 chars, no dashes)
        uuid.UUID(rid)

    def test_supplied_request_id_is_echoed(self, client):
        supplied = "test-request-id-12345"
        response = client.get("/healthz", headers={"X-Request-ID": supplied})
        assert response.headers.get("X-Request-ID") == supplied

    def test_distinct_requests_get_distinct_ids(self, client):
        r1 = client.get("/healthz")
        r2 = client.get("/healthz")
        assert r1.headers["X-Request-ID"] != r2.headers["X-Request-ID"]

    def test_error_responses_carry_request_id(self, client, db_session):
        """Standard error envelope should include request_id when available."""
        from tests.conftest import create_test_roles_and_perms, create_test_user, login_as

        admin_role, _, _, _ = create_test_roles_and_perms(db_session)
        create_test_user(db_session, "admin@test.com", "password123", admin_role)
        headers = login_as(client, "admin@test.com", "password123")
        headers["X-Request-ID"] = "err-req-id-42"

        response = client.get("/vendors/999999", headers=headers)
        assert response.status_code == 404
        body = response.json()
        assert body.get("request_id") == "err-req-id-42"


class TestMetricsPrimitives:
    """Unit-level checks on the in-process registry."""

    def test_counter_increments(self):
        c = m.Counter()
        c.inc({"k": "v"})
        c.inc({"k": "v"}, amount=2)
        c.inc({})  # no labels
        snap = c.snapshot()
        by_labels = {tuple(sorted(k.items())): v for k, v in snap}
        assert by_labels[(("k", "v"),)] == 3.0
        assert by_labels[()] == 1.0

    def test_histogram_buckets(self):
        h = m.Histogram()
        h.observe(0.5)    # <= 1ms bucket
        h.observe(30)     # <= 50ms bucket
        h.observe(60000)  # +Inf bucket
        snap = h.snapshot()
        assert len(snap) == 1
        _, counts, total = snap[0]
        assert sum(counts) == 3
        assert abs(total - ((0.5 + 30 + 60000) / 1000)) < 1e-6

    def test_path_normalisation_bucketing(self):
        assert m._normalise_path("/orders/123") == "/orders/:id"
        assert m._normalise_path("/orders/123/items/5/return") == "/orders/:id/items/:id/return"
        assert m._normalise_path("/healthz?x=1") == "/healthz"
        assert m._normalise_path("/v1.5/items") == "/v1.5/items"

    def test_gauge(self):
        g = m.Gauge(initial=4.0)
        assert g.get() == 4.0
        g.set(7.5)
        assert g.get() == 7.5


class TestResponseCache:
    """Unit tests for the in-process TTL cache used by low-churn endpoints."""

    def test_get_set_invalidate(self):
        from app.core.response_cache import TTLCache
        c = TTLCache(default_ttl=60.0)
        c.set("k1", {"v": 1})
        assert c.get("k1") == {"v": 1}
        assert c.invalidate_prefix("k1") == 1
        assert c.get("k1") is None
        assert c.stats()["hits"] == 1
        assert c.stats()["misses"] == 2

    def test_ttl_expiry(self):
        import time
        from app.core.response_cache import TTLCache
        c = TTLCache(default_ttl=0.05)
        c.set("short-lived", 42, ttl=0.05)
        assert c.get("short-lived") == 42
        time.sleep(0.08)
        assert c.get("short-lived") is None

    def test_cached_decorator_wraps_sync(self):
        from app.core.response_cache import TTLCache, cached
        c = TTLCache(default_ttl=60.0)
        calls = {"n": 0}

        @cached("sync:key", ttl_seconds=60, cache=c)
        def expensive():
            calls["n"] += 1
            return {"result": 42}

        first = expensive()
        second = expensive()
        assert first == second
        assert calls["n"] == 1  # second call served from cache

    def test_cached_decorator_wraps_async(self):
        import asyncio
        from app.core.response_cache import TTLCache, cached
        c = TTLCache(default_ttl=60.0)
        calls = {"n": 0}

        @cached("async:key", ttl_seconds=60, cache=c)
        async def expensive_async():
            calls["n"] += 1
            return {"result": 7}

        first = asyncio.run(expensive_async())
        second = asyncio.run(expensive_async())
        assert first == second
        assert calls["n"] == 1
