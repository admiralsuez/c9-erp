"""
Query Profiler

Hooks into SQLAlchemy to detect N+1 query patterns and track performance metrics.
Useful for development to identify optimization opportunities.
"""

import logging
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.pool import Pool

logger = logging.getLogger(__name__)


class QueryProfile:
    """Container for query statistics."""
    
    def __init__(self):
        self.total_queries = 0
        self.total_time_ms = 0.0
        self.queries_by_type: Dict[str, int] = defaultdict(int)
        self.slow_queries: List[Dict[str, Any]] = []
        self.n1_suspects: List[Dict[str, Any]] = []
        self.query_history: List[Dict[str, Any]] = []
    
    def add_query(self, query_str: str, duration_ms: float, is_slow: bool = False):
        """Record a query execution."""
        self.total_queries += 1
        self.total_time_ms += duration_ms
        
        # Categorize query type
        query_type = self._get_query_type(query_str)
        self.queries_by_type[query_type] += 1
        
        # Track slow queries
        if is_slow:
            self.slow_queries.append({
                'query': query_str[:200],  # Truncate for storage
                'duration_ms': duration_ms,
            })
        
        # Keep recent history
        self.query_history.append({
            'query': query_str[:200],
            'duration_ms': duration_ms,
            'type': query_type,
        })
        
        if len(self.query_history) > 1000:
            self.query_history.pop(0)
    
    def detect_n1_pattern(self, recent_queries: List[str]) -> bool:
        """
        Simple heuristic to detect potential N+1 patterns.
        
        Detects sequences like:
        - SELECT ... FROM users LIMIT 1
        - SELECT ... FROM orders WHERE user_id = ?  (repeated many times)
        """
        if len(recent_queries) < 2:
            return False
        
        # Look for pattern: one parent query followed by many similar child queries
        query_types = [self._get_query_type(q) for q in recent_queries[-20:]]
        type_counts = defaultdict(int)
        for qtype in query_types:
            type_counts[qtype] += 1
        
        # If one type appears 10+ times followed by different types, likely N+1
        for qtype, count in type_counts.items():
            if count >= 10 and 'SELECT' in qtype:
                return True
        
        return False
    
    @staticmethod
    def _get_query_type(query_str: str) -> str:
        """Extract high-level query type from SQL."""
        query_upper = query_str.upper().strip()
        
        if query_upper.startswith('SELECT'):
            # Try to extract table name
            if 'FROM' in query_upper:
                from_idx = query_upper.index('FROM')
                after_from = query_upper[from_idx + 4:].strip()
                table_part = after_from.split()[0].split('(')[0]
                return f"SELECT:{table_part}"
            return "SELECT"
        elif query_upper.startswith('INSERT'):
            return "INSERT"
        elif query_upper.startswith('UPDATE'):
            return "UPDATE"
        elif query_upper.startswith('DELETE'):
            return "DELETE"
        else:
            return "OTHER"
    
    def get_summary(self) -> Dict[str, Any]:
        """Return a summary of profiling results."""
        avg_time = self.total_time_ms / max(1, self.total_queries)
        
        return {
            'total_queries': self.total_queries,
            'total_time_ms': round(self.total_time_ms, 2),
            'average_query_time_ms': round(avg_time, 2),
            'queries_by_type': dict(self.queries_by_type),
            'slow_queries_count': len(self.slow_queries),
            'n1_suspects_count': len(self.n1_suspects),
            'top_slow_queries': self.slow_queries[:5],
        }
    
    def reset(self):
        """Clear all profiling data."""
        self.total_queries = 0
        self.total_time_ms = 0.0
        self.queries_by_type.clear()
        self.slow_queries.clear()
        self.n1_suspects.clear()
        self.query_history.clear()


class QueryProfiler:
    """
    SQLAlchemy event listener for query profiling.
    
    Attaches to SQLAlchemy engine to track all SQL queries,
    detect performance issues, and identify N+1 patterns.
    """
    
    # Slow query threshold in milliseconds
    SLOW_QUERY_THRESHOLD_MS = 50
    
    def __init__(self, engine: Optional[Engine] = None):
        """
        Initialize the profiler.
        
        Args:
            engine: SQLAlchemy engine to attach to (optional)
        """
        self.profile = QueryProfile()
        self.enabled = True
        self.recent_queries: List[str] = []
        
        if engine:
            self.attach(engine)
    
    def attach(self, engine: Engine):
        """Attach profiler to SQLAlchemy engine."""
        event.listen(engine, "before_cursor_execute", self._before_execute)
        event.listen(engine, "after_cursor_execute", self._after_execute)
        logger.info("Query profiler attached to engine")
    
    def _before_execute(self, conn, cursor, statement, parameters, context, executemany):
        """Called before a cursor executes a statement."""
        if not self.enabled:
            return
        
        # Store execution start time on the connection object
        conn.info.setdefault('_query_start_time', time.time())
    
    def _after_execute(self, conn, cursor, statement, parameters, context, executemany):
        """Called after a cursor executes a statement."""
        if not self.enabled:
            return
        
        start_time = conn.info.pop('_query_start_time', None)
        if start_time is None:
            return
        
        duration_ms = (time.time() - start_time) * 1000
        
        # Sanitize query (remove parameter values for logging)
        sanitized_query = self._sanitize_query(statement)
        
        # Record query
        is_slow = duration_ms > self.SLOW_QUERY_THRESHOLD_MS
        self.profile.add_query(sanitized_query, duration_ms, is_slow)
        
        # Track for N+1 detection
        self.recent_queries.append(sanitized_query)
        if len(self.recent_queries) > 100:
            self.recent_queries.pop(0)
        
        # Log slow queries
        if is_slow:
            logger.warning(
                f"Slow query ({duration_ms:.2f}ms): {sanitized_query[:100]}..."
            )
    
    @staticmethod
    def _sanitize_query(query_str: str) -> str:
        """Remove parameter markers and values from query for logging."""
        # Replace %s, ?, and :param patterns with placeholder
        import re
        query = re.sub(r'%s|\?|:\w+', '?', query_str)
        return query.replace('\n', ' ').replace('\r', '')
    
    def detect_n1(self) -> bool:
        """Check for N+1 query patterns in recent queries."""
        return self.profile.detect_n1_pattern(self.recent_queries)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get profiling summary."""
        summary = self.profile.get_summary()
        summary['n1_detected'] = self.detect_n1()
        return summary
    
    def log_summary(self):
        """Log profiling summary to logger."""
        summary = self.get_summary()
        logger.info(f"Query Profile: {summary['total_queries']} queries in {summary['total_time_ms']:.2f}ms")
        logger.info(f"  Average: {summary['average_query_time_ms']:.2f}ms per query")
        logger.info(f"  Slow queries: {summary['slow_queries_count']}")
        if summary['n1_detected']:
            logger.warning("  N+1 query pattern DETECTED!")
    
    def reset(self):
        """Reset profiling data."""
        self.profile.reset()
        self.recent_queries.clear()
    
    def disable(self):
        """Disable profiling temporarily."""
        self.enabled = False
    
    def enable(self):
        """Re-enable profiling."""
        self.enabled = True


# Global profiler instance (initialized at app startup)
_profiler: Optional[QueryProfiler] = None


def init_profiler(engine: Engine) -> QueryProfiler:
    """
    Initialize the global profiler instance.
    
    Should be called once at application startup.
    
    Args:
        engine: SQLAlchemy engine to profile
        
    Returns:
        The initialized QueryProfiler instance
    """
    global _profiler
    _profiler = QueryProfiler(engine)
    return _profiler


def get_profiler() -> Optional[QueryProfiler]:
    """Get the global profiler instance."""
    return _profiler


def log_profile_summary():
    """Log current profiling summary to logger."""
    if _profiler:
        _profiler.log_summary()


def reset_profile():
    """Reset profiling data."""
    if _profiler:
        _profiler.reset()


def get_profile_summary() -> Dict[str, Any]:
    """Get current profiling summary."""
    if _profiler:
        return _profiler.get_summary()
    return {}


class ProfileContext:
    """Context manager for profiling a block of code."""
    
    def __init__(self, name: str = "Query Block"):
        self.name = name
        self.start_time = None
        self.profiler = get_profiler()
    
    def __enter__(self):
        self.start_time = time.time()
        if self.profiler:
            initial_count = self.profiler.profile.total_queries
            self.initial_count = initial_count
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.profiler and self.start_time:
            duration_ms = (time.time() - self.start_time) * 1000
            queries_count = self.profiler.profile.total_queries - self.initial_count
            logger.info(
                f"{self.name}: {queries_count} queries in {duration_ms:.2f}ms "
                f"({duration_ms/max(1, queries_count):.2f}ms avg)"
            )


# Example usage decorator
def profile_queries(func):
    """
    Decorator to profile a function's database queries.
    
    Example:
        @profile_queries
        def get_orders(db):
            return db.query(Order).all()
    """
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        with ProfileContext(f"{func.__name__}"):
            return func(*args, **kwargs)
    
    return wrapper
