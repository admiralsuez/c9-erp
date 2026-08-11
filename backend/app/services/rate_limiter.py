"""Rate limiting utilities.

Provides a thread-safe, in-memory sliding-window rate limiter plus a
FastAPI/Starlette middleware that enforces per-IP and per-user limits and
attaches standard rate-limit headers to responses.

Limits are configurable via ``app.core.config.settings`` (``RATE_LIMIT_*``).

Note: This is a single-process, in-memory implementation. For multi-worker
deployments, swap the storage backend (e.g. Redis) without changing the
``RateLimiter`` interface.
"""
import logging
import threading
import time
from typing import Dict, List, Optional, Tuple

from starlette.datastructures import MutableHeaders
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import settings

logger = logging.getLogger(__name__)

# Standard headers added to every rate-limited response
RATE_LIMIT_HEADER_LIMIT = "X-RateLimit-Limit"
RATE_LIMIT_HEADER_REMAINING = "X-RateLimit-Remaining"
RATE_LIMIT_HEADER_RESET = "X-RateLimit-Reset"

# Paths that bypass rate limiting entirely
RATE_LIMIT_EXEMPT_PATHS = ("/docs", "/redoc", "/openapi.json", "/health", "/static", "/favicon.ico")


class RateLimitExceeded(Exception):
    """Raised when a request exceeds its configured rate limit."""

    def __init__(self, limit: int, retry_after: int, scope: str = "rate_limit"):
        self.limit = limit
        self.retry_after = retry_after
        self.scope = scope
        super().__init__(
            f"Rate limit exceeded: {limit} requests allowed. Retry in {retry_after}s."
        )


class RateLimiter:
    """Thread-safe sliding-window rate limiter keyed by arbitrary strings.

    Keys are typically ``ip:{addr}`` or ``user:{id}`` or ``email:{addr}``.
    A fixed-size window is kept per key; timestamps older than ``window``
    seconds are pruned on access.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._hits: Dict[str, List[float]] = {}

    def _prune(self, key: str, window: int, now: float) -> None:
        cutoff = now - window
        hits = self._hits.get(key)
        if not hits:
            return
        remaining = [t for t in hits if t > cutoff]
        if remaining:
            self._hits[key] = remaining
        else:
            self._hits.pop(key, None)

    def check(self, key: str, limit: int, window: int) -> Tuple[bool, int]:
        """Record a request for ``key``.

        Returns ``(allowed, retry_after)``. If ``allowed`` is ``True`` the
        request was counted and ``retry_after`` is 0. If ``False`` the request
        is rejected and ``retry_after`` is the seconds until the window resets.
        """
        now = time.time()
        with self._lock:
            self._prune(key, window, now)
            hits = self._hits.get(key, [])
            if len(hits) >= limit:
                retry_after = int(window - (now - hits[0])) + 1
                return False, retry_after
            hits.append(now)
            self._hits[key] = hits
            return True, 0

    def reset(self, key: Optional[str] = None) -> None:
        """Clear all counters (or just one key). Used by tests."""
        with self._lock:
            if key is None:
                self._hits.clear()
            else:
                self._hits.pop(key, None)

    @property
    def size(self) -> int:
        return len(self._hits)


# Shared process-wide instance
rate_limiter = RateLimiter()


def _client_ip(request: Request) -> str:
    """Best-effort client IP (handles proxies when X-Forwarded-For present)."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _is_exempt(request: Request) -> bool:
    path = request.url.path
    return any(
        path == p or path.startswith(p)
        for p in RATE_LIMIT_EXEMPT_PATHS
    )


class RateLimitMiddleware:
    """Enforces global rate limits and attaches rate-limit headers.

    - Public endpoints: ``RATE_LIMIT_PUBLIC_LIMIT`` per minute per IP.
    - Authenticated API endpoints: ``RATE_LIMIT_API_LIMIT`` per minute per user.
    - Auth-specific stricter limits (login / password reset) are enforced in
      the auth router where the request body is available.
    """

    def __init__(self, app, limiter: Optional[RateLimiter] = None) -> None:
        self.app = app
        self.limiter = limiter or rate_limiter

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        if _is_exempt(request):
            await self.app(scope, receive, send)
            return

        if not settings.RATE_LIMIT_ENABLED:
            await self.app(scope, receive, send)
            return

        ip = _client_ip(request)
        user_id = self._authenticated_user_id(request)

        if user_id is not None:
            key = f"user:{user_id}"
            limit = settings.RATE_LIMIT_API_LIMIT
            window = settings.RATE_LIMIT_API_WINDOW
        else:
            key = f"ip:{ip}"
            limit = settings.RATE_LIMIT_PUBLIC_LIMIT
            window = settings.RATE_LIMIT_PUBLIC_WINDOW

        allowed, retry_after = self.limiter.check(key, limit, window)
        if not allowed:
            logger.warning(
                "RATE LIMITED %s %s from %s (%s)", request.method, request.url.path, ip, key
            )
            response = JSONResponse(
                status_code=429,
                content={
                    "status": "error",
                    "message": "Too many requests. Please try again later.",
                    "error_code": "RATE_LIMITED",
                    "details": None,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "path": request.url.path,
                    "detail": "Too many requests. Please try again later.",
                },
            )
            response.headers[RATE_LIMIT_HEADER_LIMIT] = str(limit)
            response.headers[RATE_LIMIT_HEADER_REMAINING] = "0"
            response.headers[RATE_LIMIT_HEADER_RESET] = str(int(time.time()) + retry_after)
            response.headers["Retry-After"] = str(retry_after)
            await response(scope, receive, send)
            return

        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers.append(RATE_LIMIT_HEADER_LIMIT, str(limit))
                headers.append(RATE_LIMIT_HEADER_REMAINING, "1")
                headers.append(RATE_LIMIT_HEADER_RESET, str(int(time.time()) + window))
            await send(message)

        await self.app(scope, receive, send_with_headers)

    @staticmethod
    def _authenticated_user_id(request: Request) -> Optional[int]:
        """Extract user id from Bearer token without DB access (best-effort)."""
        auth = request.headers.get("authorization", "")
        if not auth.lower().startswith("bearer "):
            return None
        token = auth.split(" ", 1)[1].strip()
        try:
            from jose import jwt as jose_jwt
            payload = jose_jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM],
            )
            sub = payload.get("sub")
            if sub is None:
                return None
            return int(sub)
        except Exception:
            return None
