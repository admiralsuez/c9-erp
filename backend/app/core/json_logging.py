"""JSON / structured log formatter.

Switch the root logger's formatter by calling ``configure_json_logging()`` at
startup (gated by an env flag — default stays human-readable for dev).

The output is one JSON object per line with these keys:

    ts: ISO-8601 UTC timestamp
    level: log level name
    logger: logger name (e.g. "orders.workflow")
    message: formatted message
    request_id: populated when called inside a request context
    extra: arbitrary key/value pairs passed via ``logger.info(msg, extra={...})``

When the env var ``LOG_FORMAT`` is not ``json``, this module is a no-op so
local dev keeps the colour-free readable lines.
"""
from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict


class JsonFormatter(logging.Formatter):
    """Render ``LogRecord`` instances as single-line JSON."""

    # Standard LogRecord attributes we don't want to dump verbatim.
    _SKIP_KEYS = {
        "name", "msg", "args", "levelname", "levelno", "pathname",
        "filename", "module", "exc_info", "exc_text", "stack_info",
        "lineno", "funcName", "created", "msecs", "relativeCreated",
        "thread", "threadName", "processName", "process", "message",
        "asctime", "taskName",
    }

    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc)
                .isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Anything passed via ``extra={...}``
        for k, v in record.__dict__.items():
            if k in self._SKIP_KEYS or k.startswith("_"):
                continue
            try:
                json.dumps(v)
                payload[k] = v
            except (TypeError, ValueError):
                payload[k] = repr(v)

        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False, default=str)


_configured = False


def configure_json_logging() -> None:
    """Swap the root logger's formatter for the JSON formatter (idempotent)."""
    global _configured
    if _configured:
        return

    if os.getenv("LOG_FORMAT", "").lower() != "json":
        return

    formatter = JsonFormatter()
    root = logging.getLogger()
    for handler in root.handlers:
        handler.setFormatter(formatter)
    _configured = True


def configure_file_rotation(log_dir: str, *, max_files: int = 5) -> str:
    """Pre-create the daily log file and attach a rotated handler.

    Kept here so the metrics module owns all logging concerns. Caller wires
    this in during ``lifespan`` startup.
    """
    import glob as _glob
    import os as _os

    _os.makedirs(log_dir, exist_ok=True)

    existing = sorted(_glob.glob(_os.path.join(log_dir, "c9erp_*.log")))
    while len(existing) >= max_files:
        try:
            _os.unlink(existing.pop(0))
        except PermissionError:
            existing.pop(0)
            continue

    path = _os.path.join(
        log_dir, f"c9erp_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.log"
    )
    fh = logging.FileHandler(path, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(JsonFormatter())
    logging.getLogger().addHandler(fh)
    return path
