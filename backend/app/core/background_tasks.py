"""Lightweight background-task queue for non-blocking operations.

Use case: email sends (Phase 2.2's ``safe_send_templated_email``) can be
slow when SMTP is degraded, but the originating HTTP request should never
wait for them. ``enqueue_email`` schedules a worker to deliver the message
in a background thread and returns immediately.

The worker pool is sized to ``ENQUEUE_WORKERS`` (default 2) — enough to
absorb normal load, not enough to saturate SMTP connections under a burst.

This is intentionally NOT a full task queue (no Celery / RQ). When the
deployment grows past a single container, swap the worker target for
``arq`` or ``huey`` and keep the same ``enqueue_*`` surface.
"""
from __future__ import annotations

import logging
import queue
import threading
import time
import traceback
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, Optional

from app.core.metrics import record_background_task

logger = logging.getLogger("background")

_TASK_QUEUE: "queue.Queue[Task]" = queue.Queue(maxsize=1024)
_WORKERS_STARTED = False
_WORKER_COUNT = 2


@dataclass
class Task:
    name: str
    fn: Callable[..., Any]
    args: tuple
    kwargs: dict


def _worker_loop() -> None:
    """Pull tasks off the queue and run them; never raises out of the loop."""
    while True:
        task: Task = _TASK_QUEUE.get()
        try:
            task.fn(*task.args, **task.kwargs)
            record_background_task(name=task.name, status="ok")
        except Exception:
            record_background_task(name=task.name, status="error")
            logger.exception(
                "Background task %s failed\n%s", task.name, traceback.format_exc(),
            )
        finally:
            _TASK_QUEUE.task_done()


def start_workers(count: int = 2) -> None:
    """Spawn ``count`` worker threads. Idempotent."""
    global _WORKERS_STARTED, _WORKER_COUNT
    if _WORKERS_STARTED:
        return
    _WORKER_COUNT = count
    for i in range(count):
        t = threading.Thread(target=_worker_loop, name=f"bg-worker-{i}", daemon=True)
        t.start()
    _WORKERS_STARTED = True
    logger.info("Background worker pool started (%d workers)", count)


def enqueue(name: str, fn: Callable[..., Any], *args, **kwargs) -> bool:
    """Schedule ``fn`` to run in the background.

    Returns ``True`` if the task was queued, ``False`` if the queue is full
    (callers should log / retry but NOT fail the user-facing request).
    """
    if not _WORKERS_STARTED:
        start_workers()
    try:
        _TASK_QUEUE.put_nowait(Task(name=name, fn=fn, args=args, kwargs=kwargs))
        return True
    except queue.Full:
        logger.warning(
            "Background queue full — dropping task %s (args=%s)", name, args,
        )
        return False


def queue_size() -> int:
    return _TASK_QUEUE.qsize()


def worker_count() -> int:
    return _WORKER_COUNT


# ============ Email-specific helper ============

def enqueue_email(
    to_email: str,
    template: Any,
    context: Dict[str, Any],
    attachments: Any = None,
    context_label: str = "email",
) -> None:
    """Queue a templated email without blocking the request thread."""
    from app.services.email_service import safe_send_templated_email

    enqueue(
        name=f"email:{context_label}",
        fn=safe_send_templated_email,
        to_email=to_email,
        template=template,
        context=context,
        attachments=attachments,
        context_label=context_label,
    )
