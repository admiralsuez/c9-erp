"""
Database Query Optimization Helper for Phase 7.

Provides utilities for query optimization, indexing, and performance analysis.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, timezone
import logging
import time

try:
    from sqlalchemy import inspect, event, exc
    from sqlalchemy.orm import Session
except ImportError:
    Session = object  # Fallback for type hints

logger = logging.getLogger(__name__)


class QueryProfiler:
    """Profile query performance."""
    
    def __init__(self):
        self.queries = []
        self.total_time = 0
    
    def add_query(self, query_string: str, duration: float):
        """Add profiled query."""
        self.queries.append({
            'query': query_string,
            'duration': duration,
            'timestamp': datetime.now(timezone.utc)
        })
        self.total_time += duration
    
    def get_slow_queries(self, threshold_ms: float = 100) -> List[Dict]:
        """Get queries slower than threshold."""
        return [q for q in self.queries if q['duration'] * 1000 > threshold_ms]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get profiling statistics."""
        if not self.queries:
            return {'total_queries': 0, 'total_time': 0}
        
        durations = [q['duration'] for q in self.queries]
        
        return {
            'total_queries': len(self.queries),
            'total_time': self.total_time,
            'average_time': sum(durations) / len(durations),
            'min_time': min(durations),
            'max_time': max(durations),
            'slow_queries': len(self.get_slow_queries()),
        }


class DatabaseOptimizer:
    """Database optimization helper."""
    
    def __init__(self, db: Session):
        self.db = db
        self.profiler = QueryProfiler()
    
    def enable_query_profiling(self):
        """Enable query profiling for performance analysis."""
        try:
            @event.listens_for(self.db.get_bind(), 'before_cursor_execute')
            def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
                conn.info.setdefault('query_start_time', []).append(time.time())
            
            @event.listens_for(self.db.get_bind(), 'after_cursor_execute')
            def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
                total_time = time.time() - conn.info['query_start_time'].pop(-1)
                self.profiler.add_query(statement, total_time)
            
            logger.info("Query profiling enabled")
        except Exception as e:
            logger.warning(f"Failed to enable query profiling: {e}")
    
    def analyze_indexes(self, model_class) -> Dict[str, Any]:
        """
        Analyze indexes for a model.
        
        Args:
            model_class: SQLAlchemy model class
            
        Returns:
            Dictionary with index information
        """
        try:
            mapper = inspect(model_class)
            table = mapper.local_table
            
            indexes_info = {
                'model': model_class.__name__,
                'table': table.name,
                'indexes': []
            }
            
            for index in table.indexes:
                columns = [col.name for col in index.columns]
                indexes_info['indexes'].append({
                    'name': index.name,
                    'columns': columns,
                    'unique': index.unique,
                })
            
            return indexes_info
        except Exception as e:
            logger.error(f"Error analyzing indexes: {e}")
            return {}
    
    def suggest_indexes(self, model_class) -> List[Dict]:
        """
        Suggest indexes based on common query patterns.
        
        Args:
            model_class: SQLAlchemy model class
            
        Returns:
            List of suggested indexes
        """
        suggestions = []
        
        # Common fields that benefit from indexing
        index_candidates = {
            'id': False,  # Usually already indexed
            'created_at': True,  # Sort/filter operations
            'deleted_at': True,  # Soft deletes
            'status': True,  # Frequent filtering
            'vendor_id': True,  # Foreign key
            'user_id': True,  # Foreign key
            'order_id': True,  # Foreign key
        }
        
        try:
            mapper = inspect(model_class)
            existing_indexes = set()
            
            for index in mapper.local_table.indexes:
                for col in index.columns:
                    existing_indexes.add(col.name)
            
            for attr_name, should_index in index_candidates.items():
                if should_index and hasattr(model_class, attr_name):
                    if attr_name not in existing_indexes:
                        suggestions.append({
                            'model': model_class.__name__,
                            'column': attr_name,
                            'reason': 'Common query field',
                            'priority': 'high' if attr_name in ['created_at', 'status', 'deleted_at'] else 'medium'
                        })
        except Exception as e:
            logger.warning(f"Error suggesting indexes: {e}")
        
        return suggestions
    
    def optimize_eager_loading(self, query, relationships: List[str]):
        """
        Optimize query with eager loading.
        
        Args:
            query: SQLAlchemy query object
            relationships: List of relationship names to eagerly load
            
        Returns:
            Optimized query
        """
        try:
            from sqlalchemy.orm import joinedload
            
            for rel in relationships:
                query = query.options(joinedload(rel))
            
            return query
        except Exception as e:
            logger.warning(f"Error optimizing with eager loading: {e}")
            return query
    
    def add_pagination(self, query, skip: int = 0, limit: int = 100):
        """
        Add pagination to query.
        
        Args:
            query: SQLAlchemy query
            skip: Number of records to skip
            limit: Maximum number of records
            
        Returns:
            Paginated query
        """
        return query.offset(skip).limit(limit)
    
    def get_profiling_stats(self) -> Dict[str, Any]:
        """Get query profiling statistics."""
        stats = self.profiler.get_stats()
        slow_queries = self.profiler.get_slow_queries()
        
        return {
            'stats': stats,
            'slow_queries_count': len(slow_queries),
            'slow_queries_sample': slow_queries[:5],  # First 5 slow queries
        }


class QueryOptimizationContext:
    """Context manager for query optimization."""
    
    def __init__(self, db: Session):
        self.db = db
        self.optimizer = DatabaseOptimizer(db)
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        self.optimizer.enable_query_profiling()
        return self.optimizer
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.time() - self.start_time
        stats = self.optimizer.get_profiling_stats()
        
        logger.info(f"Query optimization context finished in {elapsed:.2f}s")
        logger.info(f"Query stats: {stats['stats']}")
        
        if stats['slow_queries_sample']:
            logger.warning(f"Found {stats['slow_queries_count']} slow queries")
            for query in stats['slow_queries_sample']:
                logger.warning(f"Slow query ({query['duration']*1000:.0f}ms): {query['query'][:100]}")


class IndexOptimization:
    """Index optimization recommendations."""
    
    RECOMMENDED_INDEXES = {
        'Order': ['status', 'created_at', 'vendor_id', 'deleted_at'],
        'InventoryItem': ['sku', 'created_at', 'deleted_at', 'is_active'],
        'Vendor': ['name', 'is_active', 'deleted_at'],
        'User': ['email', 'role', 'is_active'],
        'OrderItem': ['order_id', 'item_id'],
        'Document': ['order_id', 'created_at', 'type'],
        'EmailLog': ['created_at', 'status', 'recipient'],
        'AuditLog': ['user_id', 'created_at', 'action'],
    }
    
    @staticmethod
    def get_recommended_indexes(model_name: str) -> List[str]:
        """Get recommended indexes for a model."""
        return IndexOptimization.RECOMMENDED_INDEXES.get(model_name, [])


class PerformanceMonitor:
    """Monitor database performance metrics."""
    
    def __init__(self):
        self.metrics = {
            'query_count': 0,
            'total_query_time': 0,
            'errors': 0,
            'slow_queries': 0,
        }
        self.start_time = datetime.now(timezone.utc)
    
    def record_query(self, duration: float, is_error: bool = False, is_slow: bool = False):
        """Record a query execution."""
        self.metrics['query_count'] += 1
        self.metrics['total_query_time'] += duration
        if is_error:
            self.metrics['errors'] += 1
        if is_slow:
            self.metrics['slow_queries'] += 1
    
    def get_report(self) -> Dict[str, Any]:
        """Get performance report."""
        uptime = datetime.now(timezone.utc) - self.start_time
        
        return {
            'uptime_seconds': uptime.total_seconds(),
            'total_queries': self.metrics['query_count'],
            'total_query_time_seconds': self.metrics['total_query_time'],
            'average_query_time_ms': (
                self.metrics['total_query_time'] * 1000 / self.metrics['query_count']
                if self.metrics['query_count'] > 0 else 0
            ),
            'error_count': self.metrics['errors'],
            'slow_query_count': self.metrics['slow_queries'],
        }
    
    def get_health_status(self) -> str:
        """Get health status based on metrics."""
        report = self.get_report()
        
        if report['error_count'] > 10:
            return "critical"
        elif report['slow_query_count'] > 50:
            return "degraded"
        elif report['average_query_time_ms'] > 500:
            return "slow"
        else:
            return "healthy"


class DatabaseConnectionPool:
    """Database connection pool optimization."""
    
    def __init__(self, engine):
        self.engine = engine
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics."""
        try:
            pool = self.engine.pool
            
            return {
                'pool_size': getattr(pool, 'pool_size', 'N/A'),
                'max_overflow': getattr(pool, 'max_overflow', 'N/A'),
                'checked_out': getattr(pool, 'checkedout', lambda: 'N/A')(),
                'checked_in': getattr(pool, 'checkedin', lambda: 'N/A')(),
            }
        except Exception as e:
            logger.error(f"Error getting pool stats: {e}")
            return {}


def get_database_optimizer(db: Session) -> DatabaseOptimizer:
    """Factory function for database optimizer."""
    return DatabaseOptimizer(db)


def get_performance_monitor() -> PerformanceMonitor:
    """Factory function for performance monitor."""
    return PerformanceMonitor()
