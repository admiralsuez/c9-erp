"""
API Caching Layer Service for Phase 7.

Implements result caching for analytics queries and API responses using cachetools.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Callable, Optional
import logging
import hashlib
import json

try:
    from cachetools import TTLCache, LRUCache, Cache
except ImportError:
    pass

logger = logging.getLogger(__name__)


class CacheConfig:
    """Configuration for cache behavior."""
    
    def __init__(
        self,
        ttl_seconds: int = 300,  # 5 minutes
        max_size: int = 1000,
        cache_type: str = 'ttl'  # 'ttl', 'lru', 'simple'
    ):
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self.cache_type = cache_type


class CacheService:
    """Service for caching API responses and query results."""
    
    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self.cache = self._create_cache()
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
        }
    
    def _create_cache(self) -> Cache:
        """Create cache based on configuration."""
        try:
            if self.config.cache_type == 'ttl':
                return TTLCache(
                    maxsize=self.config.max_size,
                    ttl=self.config.ttl_seconds
                )
            elif self.config.cache_type == 'lru':
                return LRUCache(maxsize=self.config.max_size)
            else:
                # Simple dict-based cache (no expiration)
                return {}
        except Exception as e:
            logger.warning(f"Failed to create cache: {e}, using simple dict")
            return {}
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        try:
            if key in self.cache:
                entry = self.cache[key]
                # Support ttl_override by checking expiry tuple
                if isinstance(entry, tuple) and len(entry) == 2:
                    value, expiry = entry
                    if expiry is not None and datetime.now(timezone.utc) > expiry:
                        del self.cache[key]
                        self.stats['misses'] += 1
                        return None
                    self.stats['hits'] += 1
                    logger.debug(f"Cache hit for key: {key}")
                    return value
                self.stats['hits'] += 1
                logger.debug(f"Cache hit for key: {key}")
                return entry
            else:
                self.stats['misses'] += 1
                logger.debug(f"Cache miss for key: {key}")
                return None
        except Exception as e:
            logger.error(f"Error getting from cache: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl_override: Optional[int] = None):
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_override: Override TTL for this key (in seconds)
        """
        try:
            if ttl_override is not None:
                expiry = datetime.now(timezone.utc) + timedelta(seconds=ttl_override)
                self.cache[key] = (value, expiry)
            else:
                self.cache[key] = value
            self.stats['sets'] += 1
            logger.debug(f"Cached value for key: {key}")
        except Exception as e:
            logger.error(f"Error setting cache: {e}")
    
    def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key was found and deleted
        """
        try:
            if key in self.cache:
                del self.cache[key]
                logger.debug(f"Deleted cache entry: {key}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting from cache: {e}")
            return False
    
    def clear(self):
        """Clear all cache entries."""
        try:
            self.cache.clear()
            logger.info("Cache cleared")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'total_requests': total_requests,
            'hit_rate_percent': round(hit_rate, 2),
            'total_sets': self.stats['sets'],
            'cache_size': len(self.cache),
        }
    
    # Sentinel to distinguish None results from cache misses
    _SENTINEL = object()

    def cached(
        self,
        ttl: Optional[int] = None,
        key_prefix: str = ""
    ):
        """
        Decorator for caching function results.
        
        Args:
            ttl: Time to live in seconds (overrides config)
            key_prefix: Prefix for cache key
            
        Returns:
            Decorator function
        """
        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs) -> Any:
                # Generate cache key
                cache_key = self._generate_cache_key(
                    func.__name__,
                    args,
                    kwargs,
                    key_prefix
                )
                
                # Try to get from cache
                cached_value = self.get(cache_key)
                if cached_value is not self._SENTINEL:
                    return cached_value
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Cache result (use tuple wrapper to distinguish None from cache miss)
                self.set(cache_key, result if result is not None else self._SENTINEL, ttl)
                
                return result
            
            return wrapper
        return decorator
    
    def _generate_cache_key(
        self,
        func_name: str,
        args: tuple,
        kwargs: dict,
        prefix: str = ""
    ) -> str:
        """
        Generate cache key from function name and arguments.
        
        Args:
            func_name: Function name
            args: Positional arguments
            kwargs: Keyword arguments
            prefix: Optional prefix
            
        Returns:
            Cache key string
        """
        try:
            # Filter out non-serializable arguments
            serializable_args = []
            for arg in args:
                if isinstance(arg, (str, int, float, bool, type(None))):
                    serializable_args.append(arg)
                elif hasattr(arg, 'id'):
                    # For ORM objects, use their ID
                    serializable_args.append(f"obj_{arg.id}")
                else:
                    serializable_args.append(str(type(arg)))
            
            serializable_kwargs = {}
            for k, v in kwargs.items():
                if isinstance(v, (str, int, float, bool, type(None))):
                    serializable_kwargs[k] = v
                elif hasattr(v, 'id'):
                    serializable_kwargs[k] = f"obj_{v.id}"
                else:
                    serializable_kwargs[k] = str(type(v))
            
            # Create key
            key_parts = [prefix, func_name, str(serializable_args), str(serializable_kwargs)]
            key_string = "|".join(filter(None, key_parts))
            
            # Hash if too long
            if len(key_string) > 200:
                hash_obj = hashlib.md5(key_string.encode())
                return f"{prefix}:{hash_obj.hexdigest()}"
            
            return key_string
        except Exception as e:
            logger.warning(f"Error generating cache key: {e}")
            return f"{prefix}:{func_name}:{datetime.now(timezone.utc).timestamp()}"


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
