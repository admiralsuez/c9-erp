"""Analytics service with pre-built queries for dashboards and reporting."""

import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import func, and_, or_

from app.models import Order, OrderItem, InventoryItem, Vendor, User, EmailLog, AuditLog

logger = logging.getLogger(__name__)


class OverviewMetricsMixin:
    """Overview, order metrics and dashboard aggregation."""

    def get_total_orders(self, date_from=None, date_to=None) -> int:
        query = self.db.query(Order).filter(Order.deleted_at == None)
        query = self._date_filter(query, date_from, date_to)
        return query.count()

    def get_pending_approvals(self, date_from=None, date_to=None) -> int:
        query = self.db.query(Order).filter(
            Order.status == "signed_requisition_uploaded",
            Order.deleted_at == None
        )
        query = self._date_filter(query, date_from, date_to)
        return query.count()

    def get_orders_by_status(self, date_from=None, date_to=None) -> dict:
        query = self.db.query(
            Order.status,
            func.count(Order.id).label("count")
        ).filter(Order.deleted_at == None)
        query = self._date_filter(query, date_from, date_to)
        statuses = query.group_by(Order.status).all()
        return {status: count for status, count in statuses}

    def get_recent_orders(self, limit: int = 10, date_from=None, date_to=None) -> list:
        query = self.db.query(Order).filter(Order.deleted_at == None)
        query = self._date_filter(query, date_from, date_to)
        return query.order_by(Order.created_at.desc()).limit(limit).all()

    def get_order_metrics(self, date_from=None, date_to=None) -> dict:
        return {
            "total_orders": self.get_total_orders(date_from, date_to),
            "by_status": self.get_orders_by_status(date_from, date_to),
            "pending_approvals": self.get_pending_approvals(date_from, date_to),
            "average_approval_time_days": self._get_avg_approval_time(),
            "average_dispatch_time_days": self._get_avg_dispatch_time(),
        }

    def _get_avg_approval_time(self) -> float:
        """Calculate average time from requisition submission to approval."""
        try:
            approved_orders = self.db.query(Order).options(
                joinedload(Order.timeline_entries)
            ).filter(
                Order.status.in_(["approved", "dispatched", "delivered", "closed"]),
                Order.deleted_at == None
            ).all()
        except Exception:
            # If eager loading fails, use lazy load
            approved_orders = self.db.query(Order).filter(
                Order.status.in_(["approved", "dispatched", "delivered", "closed"]),
                Order.deleted_at == None
            ).all()
        
        if not approved_orders:
            return 0
        
        total_days = 0
        count = 0
        
        for order in approved_orders:
            # Find requisition_generated and approved timeline entries
            timeline = order.timeline_entries
            requisition_date = None
            approval_date = None
            
            for entry in timeline:
                if entry.action == "requisition_generated":
                    requisition_date = entry.created_at
                elif entry.action == "approved":
                    approval_date = entry.created_at
            
            if requisition_date and approval_date:
                days = (approval_date - requisition_date).days
                total_days += days
                count += 1
        
        return round(total_days / count, 2) if count > 0 else 0

    def _get_avg_dispatch_time(self) -> float:
        """Calculate average time from approval to dispatch."""
        try:
            dispatched_orders = self.db.query(Order).options(
                joinedload(Order.timeline_entries)
            ).filter(
                Order.status.in_(["dispatched", "delivered", "closed"]),
                Order.deleted_at == None
            ).all()
        except Exception:
            # If eager loading fails, use lazy load
            dispatched_orders = self.db.query(Order).filter(
                Order.status.in_(["dispatched", "delivered", "closed"]),
                Order.deleted_at == None
            ).all()
        
        if not dispatched_orders:
            return 0
        
        total_days = 0
        count = 0
        
        for order in dispatched_orders:
            timeline = order.timeline_entries
            approval_date = None
            dispatch_date = None
            
            for entry in timeline:
                if entry.action == "approved":
                    approval_date = entry.created_at
                elif entry.action == "dispatched":
                    dispatch_date = entry.created_at
            
            if approval_date and dispatch_date:
                days = (dispatch_date - approval_date).days
                total_days += days
                count += 1
        
        return round(total_days / count, 2) if count > 0 else 0

    def get_dashboard_overview(self, date_from=None, date_to=None) -> dict:
        period_days = 30
        if date_from and date_to:
            period_days = max(1, (date_to - date_from).days)
        
        try:
            # Get recent orders and serialize them
            recent = self.get_recent_orders(5, date_from, date_to)
            recent_orders_data = [
                {
                    "id": o.id,
                    "order_number": o.order_number,
                    "vendor_id": o.vendor_id,
                    "vendor_name": o.vendor.name if o.vendor else "",
                    "status": o.status,
                    "created_at": o.created_at.isoformat() if o.created_at else "",
                    "item_count": len(o.items) if o.items else 0,
                }
                for o in recent
            ]
        except Exception as e:
            logger.error(f"Error getting recent orders: {e}")
            recent_orders_data = []
        
        try:
            order_metrics = self.get_order_metrics(date_from, date_to)
        except Exception as e:
            logger.error(f"Error getting order metrics: {e}")
            order_metrics = {"total_orders": 0, "by_status": {}, "pending_approvals": 0, "average_approval_time_days": 0, "average_dispatch_time_days": 0}
        
        try:
            inventory_health = self.get_inventory_health()
        except Exception as e:
            logger.error(f"Error getting inventory health: {e}")
            inventory_health = {"total_items": 0, "low_stock_count": 0, "low_stock_items": [], "total_quantity": 0}
        
        try:
            vendor_perf = self.get_vendor_performance()
        except Exception as e:
            logger.error(f"Error getting vendor performance: {e}")
            vendor_perf = []
        
        try:
            email_stats = self.get_email_stats(period_days)
        except Exception as e:
            logger.error(f"Error getting email stats: {e}")
            email_stats = {"period_days": period_days, "total_emails": 0, "by_status": {}, "failed_count": 0, "sent_count": 0}
        
        try:
            user_activity = self.get_user_activity(period_days)
        except Exception as e:
            logger.error(f"Error getting user activity: {e}")
            user_activity = {"period_days": period_days, "active_users": 0, "total_actions": 0, "orders_created": 0, "top_actions": {}}
        
        return {
            "overview": {
                "total_orders": order_metrics.get("total_orders", 0),
                "pending_approvals": order_metrics.get("pending_approvals", 0),
                "recent_orders": recent_orders_data,
            },
            "order_metrics": order_metrics,
            "inventory_health": inventory_health,
            "vendor_performance": vendor_perf,
            "email_stats": email_stats,
            "user_activity": user_activity,
            "calculated_at": datetime.now(timezone.utc).isoformat(),
        }
