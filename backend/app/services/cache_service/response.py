"""HTTP response cache."""

from typing import Dict, Optional, Any
import hashlib
import json
import logging

from app.services.cache_service.service import CacheService

logger = logging.getLogger(__name__)

class ResponseCache:
    """Cache for HTTP responses."""
    
    def __init__(self, cache_service: Optional[CacheService] = None):
        self.cache_service = cache_service or CacheService()
        self.response_keys = {}
    
    def cache_response(
        self,
        endpoint: str,
        method: str,
        params: Optional[Dict] = None,
        response_data: Any = None,
        ttl: Optional[int] = None
    ) -> str:
        """
        Cache HTTP response.
        
        Args:
            endpoint: API endpoint
            method: HTTP method
            params: Query parameters
            response_data: Response data to cache
            ttl: Time to live in seconds
            
        Returns:
            Cache key
        """
        key = self._generate_response_key(endpoint, method, params)
        self.cache_service.set(key, response_data, ttl)
        if endpoint not in self.response_keys:
            self.response_keys[endpoint] = set()
        self.response_keys[endpoint].add(key)
        logger.debug(f"Cached response for {method} {endpoint}")
        return key
    
    def get_cached_response(
        self,
        endpoint: str,
        method: str,
        params: Optional[Dict] = None
    ) -> Optional[Any]:
        """
        Get cached HTTP response.
        
        Args:
            endpoint: API endpoint
            method: HTTP method
            params: Query parameters
            
        Returns:
            Cached response data or None
        """
        key = self._generate_response_key(endpoint, method, params)
        return self.cache_service.get(key)
    
    def invalidate_endpoint(self, endpoint: str):
        """Invalidate cache for endpoint."""
        if endpoint in self.response_keys:
            for key in self.response_keys[endpoint]:
                self.cache_service.delete(key)
            del self.response_keys[endpoint]
            logger.debug(f"Invalidated cache for {endpoint}")
    
    def _generate_response_key(
        self,
        endpoint: str,
        method: str,
        params: Optional[Dict] = None
    ) -> str:
        """Generate cache key for response."""
        parts = [method, endpoint]
        if params:
            params_str = json.dumps(params, sort_keys=True, default=str)
            parts.append(params_str)
        
        key_string = "|".join(parts)
        
        if len(key_string) > 200:
            hash_obj = hashlib.md5(key_string.encode())
            return f"response:{hash_obj.hexdigest()}"
        
        return f"response:{key_string}"
