from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db, engine
from app.core.auth import get_current_user, require_admin
from app.models import User, Settings as SettingsModel, InventoryItem, Order, AuditLog
from app.schemas import SettingsResponse, SettingsUpdate
from datetime import datetime, timezone, timedelta
import os

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("", response_model=SettingsResponse)
def get_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get company settings."""
    settings = db.query(SettingsModel).first()
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Settings not found. Run seed data first."
        )
    return settings


@router.patch("", response_model=SettingsResponse)
def update_settings(
    settings_data: SettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update company settings (admin only)."""
    settings = db.query(SettingsModel).first()
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Settings not found. Run seed data first."
        )
    
    # Update only provided fields
    update_data = settings_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(settings, field, value)
    
    db.commit()
    db.refresh(settings)
    return settings


@router.get("/system-info")
def get_system_info(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get system information (admin only)."""
    total_users = db.query(func.count(User.id)).filter(User.deleted_at == None).scalar() or 0
    total_items = db.query(func.count(InventoryItem.id)).filter(InventoryItem.deleted_at == None).scalar() or 0
    total_orders = db.query(func.count(Order.id)).filter(Order.deleted_at == None).scalar() or 0

    cutoff_30d = datetime.now(timezone.utc) - timedelta(days=30)
    active_users_30d = db.query(func.count(func.distinct(AuditLog.user_id))).filter(
        AuditLog.created_at >= cutoff_30d
    ).scalar() or 0

    db_path = ""
    db_size_mb = 0
    try:
        db_url = str(engine.url)
        if db_url.startswith("sqlite:///"):
            db_path = db_url.replace("sqlite:///", "")
            if os.path.exists(db_path):
                db_size_mb = round(os.path.getsize(db_path) / (1024 * 1024), 2)
    except Exception:
        pass

    settings = db.query(SettingsModel).first()
    updated_at = settings.updated_at.isoformat() if settings and settings.updated_at else None

    return {
        "system_version": "2.1.0",
        "last_updated": updated_at,
        "database_size_mb": db_size_mb,
        "total_users": total_users,
        "total_items": total_items,
        "total_orders": total_orders,
        "active_users_30d": active_users_30d,
    }
