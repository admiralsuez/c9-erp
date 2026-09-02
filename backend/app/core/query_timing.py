"""SQLAlchemy event hooks for query timing + slow-query logging.

Wire ``install_query_timing()`` once at process startup. It attaches two
listeners:

* ``before_cursor_execute`` — record the start time on the connection.
* ``after_cursor_execute``  — compute elapsed milliseconds, push to the
  metrics histogram, and log a warning if the query took longer than
  ``SLOW_QUERY_THRESHOLD_MS`` (default 500ms).

This is non-invasive: it does not modify the SQL, transaction state, or
result objects.
"""
from __future__ import annotations

import logging
import time
from typing import Optional

from sqlalchemy import event
from sqlalchemy.engine import Connection
from sqlalchemy.engine.interfaces import DBAPIConnection

from app.core.metrics import record_db_query
from app.core.database import engine

logger = logging.getLogger("observability.sql")

# Queries that take longer than this are logged as a warning. The Prometheus
# histogram covers all queries; this constant just controls how loud we are
# about the bad ones in plain-text logs.
SLOW_QUERY_THRESHOLD_MS = 500

_installed = False


def install_query_timing(bind: Optional[Connection] = None) -> None:
    """Attach the timing listeners. Idempotent — second call is a no-op."""
    global _installed
    if _installed:
        return

    target = bind or engine

    @event.listens_for(target, "before_cursor_execute")
    def _before(conn, cursor, statement, parameters, context, executemany):  # noqa: D401
        conn.info["_query_start"] = time.time()

    @event.listens_for(target, "after_cursor_execute")
    def _after(conn, cursor, statement, parameters, context, executemany):  # noqa: D401
        start = conn.info.pop("_query_start", None)
        if start is None:
            return
        elapsed_ms = (time.time() - start) * 1000

        # Infer operation from the leading verb of the statement.
        op = (statement.strip().split(None, 1)[0] or "other").upper()
        record_db_query(op, elapsed_ms)

        if elapsed_ms > SLOW_QUERY_THRESHOLD_MS:
            preview = (statement or "").replace("\n", " ").strip()
            if len(preview) > 300:
                preview = preview[:300] + "...[truncated]"
            logger.warning(
                "SLOW QUERY (%.1fms) %s",
                elapsed_ms, preview,
            )

    _installed = True
