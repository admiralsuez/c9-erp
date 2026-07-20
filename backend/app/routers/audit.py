from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models import User, AuditLog

from typing import Optional

router = APIRouter(prefix="/audit-logs", tags=["Audit"])


@router.get("")
def list_audit_logs(
    user_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List audit logs."""
    query = db.query(AuditLog)
    
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    
    if action:
        query = query.filter(AuditLog.action.ilike(f"%{action}%"))
    
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    
    total = query.count()
    pages = (total + size - 1) // size if total > 0 else 0
    skip = (page - 1) * size
    logs = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(size).all()
    
    return {
        "items": logs,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages,
    }
