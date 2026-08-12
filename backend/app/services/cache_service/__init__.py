"""API caching layer service.

Split from the former app/services/cache_service.py monolith into focused
modules. All public names are re-exported here so existing imports keep working.
"""

from app.services.cache_service.service import CacheConfig, CacheService
from app.services.cache_service.analytics import AnalyticsCacheService
from app.services.cache_service.response import ResponseCache
from app.services.cache_service.query import QueryCache
from app.services.cache_service.factories import (
    get_cache_service,
    get_analytics_cache_service,
    get_response_cache,
    get_query_cache,
)

__all__ = [
    "CacheConfig",
    "CacheService",
    "AnalyticsCacheService",
    "ResponseCache",
    "QueryCache",
    "get_cache_service",
    "get_analytics_cache_service",
    "get_response_cache",
    "get_query_cache",
]
