"""Cache service factories."""

from typing import Optional

from app.services.cache_service.service import CacheConfig, CacheService
from app.services.cache_service.analytics import AnalyticsCacheService
from app.services.cache_service.response import ResponseCache
from app.services.cache_service.query import QueryCache

def get_cache_service(config: Optional[CacheConfig] = None) -> CacheService:
    """Factory function for cache service."""
    return CacheService(config)


def get_analytics_cache_service(config: Optional[CacheConfig] = None) -> AnalyticsCacheService:
    """Factory function for analytics cache service."""
    return AnalyticsCacheService(config)


def get_response_cache(cache_service: Optional[CacheService] = None) -> ResponseCache:
    """Factory function for response cache."""
    return ResponseCache(cache_service)


def get_query_cache(cache_service: Optional[CacheService] = None) -> QueryCache:
    """Factory function for query cache."""
    return QueryCache(cache_service)
