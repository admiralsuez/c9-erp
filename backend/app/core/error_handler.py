"""Standardized error responses and global exception handlers.

Every error raised by the application (HTTPException, validation errors,
unhandled exceptions, rate-limit rejections) is converted to a consistent
shape::

    {
        "status": "error",
        "message": "human readable message",
        "error_code": "NOT_FOUND",          # see ERROR_CODE_CATALOG
        "details": null | {...},            # optional structured detail
        "timestamp": "2026-08-11T12:00:00Z",
        "path": "/api/orders/123",
        "detail": "human readable message"  # legacy alias kept for frontend
    }

The legacy ``detail`` key mirrors ``message`` so the existing frontend and
older API consumers keep working while the new format is adopted.
"""
import logging
import time
from typing import Any, Dict, Optional

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

# Error code catalog: HTTP status -> canonical error code
ERROR_CODE_CATALOG: Dict[int, str] = {
    400: "VALIDATION_ERROR",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMITED",
    500: "INTERNAL_ERROR",
    503: "SERVICE_UNAVAILABLE",
}

DEFAULT_ERROR_CODE = "INTERNAL_ERROR"


class ErrorResponse(BaseModel):
    status: str = "error"
    message: str
    error_code: str
    details: Optional[Any] = None
    timestamp: str
    path: str
    detail: str = Field(..., description="Legacy alias of message")


def _now_utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _extract_message(detail: Any) -> str:
    """Best-effort extraction of a human readable message from a detail value."""
    if isinstance(detail, str):
        return detail
    if isinstance(detail, dict):
        return detail.get("message") or str(detail)
    if isinstance(detail, list):
        parts = []
        for item in detail:
            if isinstance(item, dict):
                parts.append(item.get("msg") or item.get("message") or str(item))
            else:
                parts.append(str(item))
        return "; ".join(parts) if parts else "Validation error"
    return "Request failed"


def _extract_details(detail: Any) -> Optional[Any]:
    if isinstance(detail, dict):
        non_message = {k: v for k, v in detail.items() if k != "message"}
        return non_message or None
    if isinstance(detail, list):
        return detail
    return None


def build_error_response(
    request: Request,
    status_code: int,
    detail: Any,
) -> Dict[str, Any]:
    """Build the standardized error body for a request."""
    return ErrorResponse(
        message=_extract_message(detail),
        error_code=ERROR_CODE_CATALOG.get(status_code, DEFAULT_ERROR_CODE),
        details=_extract_details(detail),
        timestamp=_now_utc(),
        path=request.url.path,
        detail=_extract_message(detail),
    ).model_dump()


def _json_response(request: Request, status_code: int, detail: Any, headers: Optional[dict] = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=build_error_response(request, status_code, detail),
        headers=headers,
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    status_code = exc.status_code
    logger.warning(
        "HTTP %s | %s %s | %s",
        status_code, request.method, request.url.path, _extract_message(exc.detail),
    )
    return _json_response(request, status_code, exc.detail, headers=getattr(exc, "headers", None))


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors()
    logger.warning(
        "VALIDATION | %s %s | %s",
        request.method, request.url.path, _extract_message(errors),
    )
    return _json_response(request, 422, errors)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    client = request.client.host if request.client else "unknown"
    logger.error(
        "UNHANDLED | %s %s from %s | %s",
        request.method, request.url.path, client, exc,
        exc_info=True,
    )
    return _json_response(request, 500, "Internal server error")


async def rate_limit_exception_handler(request: Request, exc) -> JSONResponse:
    retry_after = getattr(exc, "retry_after", 60)
    limit = getattr(exc, "limit", None)
    message = "Too many requests. Please try again later."
    if limit is not None:
        message = f"Rate limit exceeded: {limit} requests allowed. Retry in {retry_after}s."
    logger.warning(
        "RATE LIMITED | %s %s | %s", request.method, request.url.path, message,
    )
    return _json_response(
        request,
        429,
        {"message": message},
        headers={"Retry-After": str(retry_after)},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all standardized exception handlers on the FastAPI app."""
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
    from app.services.rate_limiter import RateLimitExceeded
    app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)
