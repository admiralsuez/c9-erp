"""Database query cache."""

from typing import Dict, Optional, Any
import logging

from app.services.cache_service.service import CacheService

logger = logging.getLogger(__name__)

class QueryCache:
    """Cache for database queries."""
    
    def __init__(self, cache_service: Optional[CacheService] = None):
        self.cache_service = cache_service or CacheService()
        self._model_keys: Dict[str, set] = {}
    
    def cache_query_result(
        self,
        model_name: str,
        query_id: str,
        result: Any
    ):
        """Cache query result."""
        key = f"query:{model_name}:{query_id}"
        self.cache_service.set(key, result)
        if model_name not in self._model_keys:
            self._model_keys[model_name] = set()
        self._model_keys[model_name].add(key)
    
    def get_query_result(
        self,
        model_name: str,
        query_id: str
    ) -> Optional[Any]:
        """Get cached query result."""
        key = f"query:{model_name}:{query_id}"
        return self.cache_service.get(key)
    
    def invalidate_model(self, model_name: str):
        """Invalidate all cached queries for a model."""
        keys = self._model_keys.pop(model_name, set())
        for key in keys:
            self.cache_service.delete(key)
        logger.debug(f"Invalidated {len(keys)} cache entries for model: {model_name}")
