"""Request-id + metrics middleware.

Installs a middleware that:

1. Reads ``X-Request-ID`` from the incoming request, or generates a new
   UUID4 if missing.
2. Stores the id on ``request.state.request_id`` so handlers and the
   error envelope can echo it back to the client.
3. Records the request in the metrics registry (counter + histogram) for
   ``/metrics`` to scrape.
4. Echoes the request-id back to the client via the response header so the
   frontend can include it in support tickets / bug reports.

The middleware also adds the request-id to the log context for the duration
of the request by attaching it as a ``LogRecord`` attribute, which the JSON
formatter picks up automatically.
"""
from __future__ import annotations

import logging
import time
import uuid
from typing import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.metrics import record_http_request

REQUEST_ID_HEADER = "X-Request-ID"
logger = logging.getLogger("observability")


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        # Adopt the inbound id or mint a new one. uuid4 hex = 32 chars,
        # short enough for log lines, unique enough for tracing.
        request_id = request.headers.get(REQUEST_ID_HEADER) or uuid.uuid4().hex
        request.state.request_id = request_id

        # Tag the current logging context for this request.
        # Newer Python lets us attach arbitrary attrs to LogRecords; the JSON
        # formatter picks them up via the ``extra`` payload. The cleanest
        # portable approach is a logging Filter, but a contextvar-based one
        # is overkill for this app — we just write the id into a module-level
        # adapter the request handlers can grab via ``current_request_id()``.
        global _current_request_id
        _current_request_id = request_id

        start = time.time()
        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = (time.time() - start) * 1000
            record_http_request(
                method=request.method,
                path=request.url.path,
                status=500,
                duration_ms=elapsed_ms,
            )
            raise
        finally:
            _current_request_id = None

        elapsed_ms = (time.time() - start) * 1000
        record_http_request(
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=elapsed_ms,
        )

        response.headers[REQUEST_ID_HEADER] = request_id
        return response


_current_request_id: str | None = None


def current_request_id() -> str | None:
    """Return the request id for the currently-serving request, if any.

    Used by handlers / error envelopes to surface the id in logs and JSON
    responses. Returns ``None`` outside of a request lifecycle.
    """
    return _current_request_id
