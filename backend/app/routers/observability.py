"""Routes for the observability surface:

* ``GET /metrics`` — Prometheus text exposition (counters + histograms).
* ``GET /healthz`` — liveness, returns 200 if the process is running.
* ``GET /readyz``  — readiness, returns 200 when the DB is reachable.

We separate liveness from readiness so Kubernetes / Docker Compose can keep
the process alive across short DB blips (liveness still passes) while the
load balancer pulls the worker from the pool until the DB is back
(readiness fails).
"""
from __future__ import annotations

import time
import logging

from fastapi import APIRouter, Response
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import engine
from app.core.metrics import render_prometheus

router = APIRouter(tags=["Observability"])
logger = logging.getLogger(__name__)


@router.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    """Prometheus scrape endpoint. No auth — restrict via reverse proxy."""
    body = render_prometheus()
    return Response(content=body, media_type="text/plain; version=0.0.4")


@router.get("/healthz", include_in_schema=False)
def healthz() -> dict:
    """Liveness probe: the process is alive and can serve requests."""
    return {"status": "ok"}


@router.get("/readyz", include_in_schema=False)
def readyz() -> Response:
    """Readiness probe: the process can talk to the database."""
    started = time.time()
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        elapsed_ms = (time.time() - started) * 1000
        return Response(
            content=f'{{"status":"ready","db_ok":true,"db_latency_ms":{elapsed_ms:.1f}}}',
            media_type="application/json",
        )
    except SQLAlchemyError as exc:
        logger.error("readyz: DB ping failed: %s", exc)
        return Response(
            content='{"status":"not_ready","db_ok":false}',
            status_code=503,
            media_type="application/json",
        )
    except Exception as exc:
        logger.exception("readyz: unexpected failure")
        return Response(
            content=f'{{"status":"not_ready","error":"{exc!s}"}}',
            status_code=503,
            media_type="application/json",
        )
