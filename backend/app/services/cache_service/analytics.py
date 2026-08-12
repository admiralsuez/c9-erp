"""Analytics-specific cache service."""

from typing import Dict, Any, Optional
import logging

from app.services.cache_service.service import CacheConfig, CacheService

logger = logging.getLogger(__name__)

class AnalyticsCacheService(CacheService):
    """Specialized cache service for analytics queries."""
    
    def __init__(self, config: Optional[CacheConfig] = None):
        # Default to longer TTL for analytics
        default_config = CacheConfig(
            ttl_seconds=600,  # 10 minutes
            max_size=500
        )
        super().__init__(config or default_config)
        self.analytics_keys = set()
    
    def cache_analytics_query(
        self,
        query_name: str,
        result: Any,
        ttl: Optional[int] = None
    ):
        """Cache analytics query result."""
        key = f"analytics:{query_name}"
        self.set(key, result, ttl)
        self.analytics_keys.add(key)
    
    def get_analytics_query(self, query_name: str) -> Optional[Any]:
        """Get cached analytics query result."""
        key = f"analytics:{query_name}"
        return self.get(key)
    
    def invalidate_analytics(self):
        """Invalidate all analytics cache."""
        for key in list(self.analytics_keys):
            self.delete(key)
        self.analytics_keys.clear()
        logger.info("Analytics cache invalidated")
    
    def get_cached_order_metrics(self) -> Optional[Dict]:
        """Get cached order metrics."""
        return self.get_analytics_query("order_metrics")
    
    def get_cached_inventory_health(self) -> Optional[Dict]:
        """Get cached inventory health."""
        return self.get_analytics_query("inventory_health")
    
    def get_cached_vendor_performance(self) -> Optional[list]:
        """Get cached vendor performance."""
        return self.get_analytics_query("vendor_performance")
    
    def get_cached_dashboard_overview(self) -> Optional[Dict]:
        """Get cached dashboard overview."""
        return self.get_analytics_query("dashboard_overview")
