"""Analytics service with pre-built queries for dashboards and reporting."""

import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import func, and_, or_

from app.models import Order, OrderItem, InventoryItem, Vendor, User, EmailLog, AuditLog

logger = logging.getLogger(__name__)


class CommunicationMetricsMixin:
    """Email stats and user activity metrics."""

    def get_email_stats(self, days: int = 30) -> dict:
        """Get email sending statistics for the past N days."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        total = self.db.query(func.count(EmailLog.id)).filter(
            EmailLog.created_at >= cutoff_date
        ).scalar() or 0
        
        by_status = dict(self.db.query(
            EmailLog.status,
            func.count(EmailLog.id)
        ).filter(
            EmailLog.created_at >= cutoff_date
        ).group_by(EmailLog.status).all())
        
        return {
            "period_days": days,
            "total_emails": total,
            "by_status": by_status,
            "failed_count": by_status.get("failed", 0),
            "sent_count": by_status.get("sent", 0),
        }

    def get_user_activity(self, days: int = 30) -> dict:
        """Get user activity metrics."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        active_users = self.db.query(func.count(func.distinct(AuditLog.user_id))).filter(
            AuditLog.created_at >= cutoff_date
        ).scalar() or 0
        
        total_actions = self.db.query(func.count(AuditLog.id)).filter(
            AuditLog.created_at >= cutoff_date
        ).scalar() or 0
        
        top_actions = dict(self.db.query(
            AuditLog.action,
            func.count(AuditLog.id)
        ).filter(
            AuditLog.created_at >= cutoff_date
        ).group_by(AuditLog.action).order_by(func.count(AuditLog.id).desc()).limit(5).all())
        
        orders_created = self.db.query(func.count(Order.id)).filter(
            Order.created_at >= cutoff_date,
            Order.deleted_at == None
        ).scalar() or 0
        
        return {
            "period_days": days,
            "active_users": active_users,
            "total_actions": total_actions,
            "orders_created": orders_created,
            "top_actions": top_actions
        }
