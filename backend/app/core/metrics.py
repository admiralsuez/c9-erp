"""Lightweight Prometheus metrics for the Cloud9 ERP API.

We avoid pulling in the full ``prometheus_client`` package (extra deps) and
implement just enough counters/histograms to power a single ``/metrics``
endpoint. Output follows the text exposition format so Prometheus /
VictoriaMetrics / Grafana Agent can scrape it directly.

Metrics exposed:

* ``http_requests_total{method,path,status}`` — counter.
* ``http_request_duration_seconds{method,path}`` — histogram (ms).
* ``db_query_duration_seconds{operation}`` — histogram.
* ``background_tasks_total{name,status}`` — counter for emails / backups.
* ``process_uptime_seconds`` — gauge.

The metrics are stored in-process; in a multi-worker setup each worker
will expose its own /metrics. The Caddy upstream health check picks one
backend per scrape so the values may differ slightly from worker to worker.
"""
from __future__ import annotations

import threading
import time
from collections import defaultdict
from typing import Dict, List, Tuple


class Counter:
    """Monotonically-increasing counter with label dimensions."""
    __slots__ = ("_values", "_lock")

    def __init__(self) -> None:
        self._values: Dict[Tuple[Tuple[str, str], ...], float] = defaultdict(float)
        self._lock = threading.Lock()

    def inc(self, labels: Dict[str, str] = None, amount: float = 1.0) -> None:
        key = tuple(sorted((labels or {}).items()))
        with self._lock:
            self._values[key] += amount

    def snapshot(self) -> List[Tuple[Dict[str, str], float]]:
        with self._lock:
            return [
                (dict(k) if k else {}, v)
                for k, v in self._values.items()
            ]


class Histogram:
    """Fixed-bucket histogram (powers of two from 1ms to ~16s)."""
    __slots__ = ("_buckets", "_counts", "_sums", "_lock")

    BUCKETS_MS = (
        1, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000, 30000,
    )

    def __init__(self) -> None:
        self._buckets = list(self.BUCKETS_MS) + [float("+inf")]
        self._counts: Dict[Tuple[Tuple[str, str], ...], List[int]] = {}
        self._sums: Dict[Tuple[Tuple[str, str], ...], float] = defaultdict(float)
        self._lock = threading.Lock()

    def observe(self, value_ms: float, labels: Dict[str, str] = None) -> None:
        key = tuple(sorted((labels or {}).items()))
        with self._lock:
            counts = self._counts.setdefault(key, [0] * len(self._buckets))
            for i, upper in enumerate(self._buckets):
                if value_ms <= upper:
                    counts[i] += 1
                    break
            self._sums[key] += value_ms / 1000.0  # store seconds for Prometheus

    def snapshot(self) -> List[Tuple[Dict[str, str], List[int], float]]:
        with self._lock:
            return [
                (dict(k) if k else {}, list(c), self._sums[k])
                for k, c in self._counts.items()
            ]


class Gauge:
    """Single-valued gauge."""
    __slots__ = ("_value", "_lock")

    def __init__(self, initial: float = 0.0) -> None:
        self._value = initial
        self._lock = threading.Lock()

    def set(self, value: float) -> None:
        with self._lock:
            self._value = value

    def get(self) -> float:
        with self._lock:
            return self._value


# ---- global registry ----
_http_requests = Counter()
_http_duration = Histogram()
_db_query_duration = Histogram()
_background_tasks = Counter()
_uptime = Gauge()

start_time = time.time()


def record_http_request(method: str, path: str, status: int, duration_ms: float) -> None:
    """Called from the request-logging middleware for every served request."""
    labels = {"method": method.upper(), "path": _normalise_path(path), "status": str(status)}
    _http_requests.inc(labels)
    _http_duration.observe(duration_ms, {"method": method.upper(), "path": _normalise_path(path)})


def record_db_query(operation: str, duration_ms: float) -> None:
    """Called from the SQLAlchemy ``before_cursor_execute`` event listener."""
    _db_query_duration.observe(duration_ms, {"operation": operation or "other"})


def record_background_task(name: str, status: str) -> None:
    """Called from background jobs (emails, backups, schedulers)."""
    _background_tasks.inc({"name": name, "status": status})


def _normalise_path(path: str) -> str:
    """Bucket dynamic IDs into placeholders so we don't blow up cardinality.

    Replaces ``/orders/123`` → ``/orders/:id`` for any trailing integer
    segment. This keeps the ``path`` label small (a few dozen buckets at most).
    """
    parts = path.split("?")[0].split("/")
    out = []
    for p in parts:
        if p.isdigit():
            out.append(":id")
        else:
            out.append(p)
    return "/".join(out) or "/"


def render_prometheus() -> str:
    """Return the entire registry as a Prometheus text-format payload."""
    from app.core.response_cache import stats as cache_stats

    lines: List[str] = []

    lines.append("# HELP http_requests_total Total HTTP requests served.")
    lines.append("# TYPE http_requests_total counter")
    for labels, value in _http_requests.snapshot():
        label_str = _format_labels(labels)
        lines.append(f"http_requests_total{{{label_str}}} {value}")

    lines.append("# HELP http_request_duration_seconds HTTP request latency in seconds.")
    lines.append("# TYPE http_request_duration_seconds histogram")
    for labels, counts, total in _http_duration.snapshot():
        label_str = _format_labels(labels)
        for upper, c in zip(_http_duration._buckets, counts):
            bucket = (
                f"http_request_duration_seconds_bucket{{{label_str},le=\"{_fmt_bucket(upper)}\"}}"
            )
            lines.append(f"{bucket} {c}")
        lines.append(f"http_request_duration_seconds_count{{{label_str}}} {sum(counts)}")
        lines.append(f"http_request_duration_seconds_sum{{{label_str}}} {total:.6f}")
        lines.append(f"http_request_duration_seconds_count{{{label_str}}} {sum(counts)}")
        lines.append(f"http_request_duration_seconds_sum{{{label_str}}} {total:.6f}")

    lines.append("# HELP db_query_duration_seconds DB query latency in seconds.")
    lines.append("# TYPE db_query_duration_seconds histogram")
    for labels, counts, total in _db_query_duration.snapshot():
        label_str = _format_labels(labels)
        for upper, c in zip(_db_query_duration._buckets, counts):
            bucket = (
                f"db_query_duration_seconds_bucket{{{label_str},le=\"{_fmt_bucket(upper)}\"}}"
            )
            lines.append(f"{bucket} {c}")
        lines.append(f"db_query_duration_seconds_count{{{label_str}}} {sum(counts)}")
        lines.append(f"db_query_duration_seconds_sum{{{label_str}}} {total:.6f}")

    lines.append("# HELP background_tasks_total Total background task runs.")
    lines.append("# TYPE background_tasks_total counter")
    for labels, value in _background_tasks.snapshot():
        label_str = _format_labels(labels)
        lines.append(f"background_tasks_total{{{label_str}}} {value}")

    cs = cache_stats()
    lines.append("# HELP response_cache_size In-process response cache entries.")
    lines.append("# TYPE response_cache_size gauge")
    lines.append(f"response_cache_size {cs['size']}")
    lines.append("# HELP response_cache_hits_total Response cache hits.")
    lines.append("# TYPE response_cache_hits_total counter")
    lines.append(f"response_cache_hits_total {cs['hits']}")
    lines.append("# HELP response_cache_misses_total Response cache misses.")
    lines.append("# TYPE response_cache_misses_total counter")
    lines.append(f"response_cache_misses_total {cs['misses']}")

    _uptime.set(time.time() - start_time)
    lines.append("# HELP process_uptime_seconds Seconds since process start.")
    lines.append("# TYPE process_uptime_seconds gauge")
    lines.append(f"process_uptime_seconds {_uptime.get():.3f}")

    return "\n".join(lines) + "\n"


def _format_labels(labels: Dict[str, str]) -> str:
    if not labels:
        return ""
    return ",".join(
        f'{k}="{_escape(v)}"' for k, v in sorted(labels.items())
    )


def _escape(value: str) -> str:
    return str(value).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _fmt_bucket(upper: float) -> str:
    if upper == float("+inf"):
        return "+Inf"
    return f"{upper / 1000:.3f}"
