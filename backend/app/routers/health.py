"""
Health check and system monitoring endpoints.
"""

import logging
import time
import psutil
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timezone
from app.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["Health & Monitoring"])


@router.get("/")
def health_check(db: Session = Depends(get_db)):
    """
    Basic health check endpoint.
    Returns system status and database connectivity.
    """
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        db_status = "healthy"
        db_message = None
    except Exception as e:
        db_status = "unhealthy"
        db_message = str(e)
    
    return {
        "status": "ok" if db_status == "healthy" else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": {
            "status": db_status,
            "message": db_message
        },
        "version": "0.1.0"
    }


@router.get("/live")
def liveness_check():
    """
    Liveness probe for Kubernetes.
    Returns 200 if service is running.
    """
    return {"status": "alive", "timestamp": datetime.now(timezone.utc).isoformat()}


@router.get("/ready")
def readiness_check(db: Session = Depends(get_db)):
    """
    Readiness probe for Kubernetes.
    Returns 200 if service is ready to handle traffic.
    """
    try:
        # Test database connection with timeout
        db.execute(text("SELECT 1"))
        return {"status": "ready", "timestamp": datetime.now(timezone.utc).isoformat()}
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        return {
            "status": "not_ready",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@router.get("/metrics")
def system_metrics():
    """
    Get system performance metrics.
    Includes CPU, memory, disk usage.
    """
    try:
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count(logical=True)
        
        # Memory metrics
        memory = psutil.virtual_memory()
        
        # Disk metrics
        disk = psutil.disk_usage("/")
        
        # Process info
        process = psutil.Process()
        process_memory = process.memory_info()
        process_cpu = process.cpu_percent(interval=0.1)
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cpu": {
                "percent": cpu_percent,
                "count": cpu_count,
                "process_percent": process_cpu
            },
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "percent": memory.percent,
                "process_mb": round(process_memory.rss / (1024**2), 2)
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "percent": disk.percent
            }
        }
    except Exception as e:
        logger.error(f"Metrics collection failed: {str(e)}")
        return {"error": str(e), "timestamp": datetime.now(timezone.utc).isoformat()}


@router.get("/database-status")
def database_status(db: Session = Depends(get_db)):
    """
    Detailed database connection status.
    Shows connection pool stats and query performance.
    """
    try:
        # Test query performance
        start = time.time()
        db.execute(text("SELECT 1"))
        query_time_ms = round((time.time() - start) * 1000, 2)
        
        # Get connection pool info if available
        pool_info = {}
        if hasattr(db.bind, 'pool'):
            pool = db.bind.pool
            pool_info = {
                "size": pool.size() if hasattr(pool, 'size') else None,
                "checked_out": pool.checkedout() if hasattr(pool, 'checkedout') else None,
                "overflow": pool.overflow() if hasattr(pool, 'overflow') else None
            }
        
        return {
            "status": "healthy",
            "query_time_ms": query_time_ms,
            "connection_pool": pool_info,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Database status check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
