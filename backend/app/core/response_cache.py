"""Tiny in-process TTL cache for read-heavy endpoints.

Why not Redis yet? The deployment runs a single backend container. A
process-local cache already cuts DB load significantly for hot endpoints
like ``GET /dashboard/summary``, ``GET /settings``, and the vendor type
list. When we go multi-worker, swap this for a Redis-backed adapter
without touching call sites.

The cache contract:

* ``cached(key, ttl_seconds, fn)`` — fetch-or-compute.
* ``invalidate(prefix)`` — drop every key starting with ``prefix`` (call
  after any write that would change cached data).
* ``stats()`` — hit/miss counters for ``/metrics``.

We deliberately do NOT cache anything containing per-user state (orders,
notifications, RBAC decisions) — only the global, role-independent lookups.
"""
from __future__ import annotations

import threading
import time
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple


class TTLCache:
    """Thread-safe TTL cache."""

    def __init__(self, default_ttl: float = 60.0, max_size: int = 512) -> None:
        self._store: Dict[str, Tuple[float, Any]] = {}
        self._lock = threading.Lock()
        self.default_ttl = default_ttl
        self.max_size = max_size
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                self._misses += 1
                return None
            expires_at, value = entry
            if expires_at < time.time():
                del self._store[key]
                self._misses += 1
                return None
            self._hits += 1
            return value

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        with self._lock:
            if len(self._store) >= self.max_size:
                # Drop the oldest by expiry; O(n) but bounded by max_size.
                oldest_key = min(self._store, key=lambda k: self._store[k][0])
                self._store.pop(oldest_key, None)
            self._store[key] = (time.time() + (ttl or self.default_ttl), value)

    def invalidate_prefix(self, prefix: str) -> int:
        """Drop every entry whose key starts with ``prefix``. Returns the count removed."""
        with self._lock:
            doomed = [k for k in self._store if k.startswith(prefix)]
            for k in doomed:
                del self._store[k]
            return len(doomed)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    def stats(self) -> Dict[str, int]:
        with self._lock:
            return {
                "size": len(self._store),
                "hits": self._hits,
                "misses": self._misses,
                "max_size": self.max_size,
            }


# Default cache for global, rarely-changing data
_cache = TTLCache(default_ttl=60.0, max_size=512)


def cached(
    key: str,
    ttl_seconds: float = 60.0,
    cache: Optional[TTLCache] = None,
):
    """Decorator wrapping a (sync or async) handler to fetch-or-compute from the cache.

    Usage::

        @router.get("/dashboard/summary")
        @cached("dashboard:summary", ttl_seconds=30)
        async def dashboard_summary(...): ...

        @router.get("/settings")
        @cached("settings", ttl_seconds=120)
        def get_settings(...): ...

    The wrapped function can be sync or async — we detect via inspection.
    Pick explicit keys; we don't auto-include parameters because per-user
    data must not be cached in this shared instance.
    """
    import asyncio
    backend = cache or _cache

    def decorator(fn):
        if asyncio.iscoroutinefunction(fn):
            async def async_wrapper(*args, **kwargs):
                hit = backend.get(key)
                if hit is not None:
                    return hit
                value = await fn(*args, **kwargs)
                if value is not None:
                    backend.set(key, value, ttl_seconds)
                return value
            return async_wrapper

        def sync_wrapper(*args, **kwargs):
            hit = backend.get(key)
            if hit is not None:
                return hit
            value = fn(*args, **kwargs)
            if value is not None:
                backend.set(key, value, ttl_seconds)
            return value
        return sync_wrapper
    return decorator


def invalidate(prefix: str) -> int:
    """Drop every cached entry starting with ``prefix``. Call after writes."""
    return _cache.invalidate_prefix(prefix)


def stats() -> Dict[str, int]:
    return _cache.stats()
