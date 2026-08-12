"""Cache key generation and invalidation helpers.

Small, dependency-light utilities for building cache keys and TTL values that
complement ``app.services.cache_service`` (Phase 7). No external cache backend
is required; these helpers work with any dict-like store.
"""
from __future__ import annotations
from typing import Any, Dict, Iterable, Optional
import hashlib
import json


def build_key(prefix: str, *parts: Any, **kwargs: Any) -> str:
    """Build a deterministic cache key from a prefix and parts.

    Parts and kwargs are rendered deterministically so the same inputs always
    produce the same key::

        build_key("order", order_id)                  # "order:123"
        build_key("inventory", item_id, page=2)       # "inventory:9:page=2"
    """
    segments = [str(prefix)]
    for part in parts:
        segments.append(_stringify(part))
    for name in sorted(kwargs):
        segments.append(f"{name}={_stringify(kwargs[name])}")
    return ":".join(segments)


def _stringify(value: Any) -> str:
    """Render a value deterministically (lists/dicts via stable JSON)."""
    if isinstance(value, dict):
        return json.dumps(value, sort_keys=True, default=str)
    if isinstance(value, (list, tuple, set)):
        return json.dumps(sorted(value, key=str), default=str)
    return str(value)


def hash_key(prefix: str, *parts: Any, **kwargs: Any) -> str:
    """Build a hashed cache key (sha256 hex) for long or sensitive inputs.

    Useful when key parts are large (query strings, serialized filters).
    """
    raw = build_key(prefix, *parts, **kwargs)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return f"{prefix}:{digest}"


def ttl_for(
    ttl: Optional[int],
    default_ttl: int = 300,
    min_ttl: int = 1,
    max_ttl: Optional[int] = None,
) -> int:
    """Clamp a TTL value into a safe range."""
    if ttl is None:
        ttl = default_ttl
    try:
        ttl = int(ttl)
    except (TypeError, ValueError):
        ttl = default_ttl
    ttl = max(min_ttl, ttl)
    if max_ttl is not None:
        ttl = min(ttl, int(max_ttl))
    return ttl


def model_key_prefix(model_name: str) -> str:
    """Return the cache-key prefix convention for a model."""
    return f"model:{model_name.lower()}"


def invalidate_keys_for(
    cache: Dict[str, Any],
    prefix: str,
) -> int:
    """Remove every key starting with ``prefix``.

    Args:
        cache: The cache mapping (e.g. ``cache_service.cache``).
        prefix: Key prefix to match (e.g. ``"model:order"``).

    Returns:
        Number of keys removed.
    """
    stale = [k for k in list(cache.keys()) if str(k).startswith(prefix)]
    for key in stale:
        cache.pop(key, None)
    return len(stale)


def entity_ids_for(namespace: str, ids: Iterable[int]) -> str:
    """Collapse a set of ids into a cache-key-safe token."""
    return f"{namespace}:{','.join(str(i) for i in sorted(set(ids)))}"
