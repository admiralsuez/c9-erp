"""
Analytics service with pre-built queries for dashboards and reporting.
"""

import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import func, and_, or_

from app.models import Order, OrderItem, InventoryItem, Vendor, User, EmailLog, AuditLog

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for analytics queries and data aggregation."""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ============ OVERVIEW METRICS ============
    
    def _date_filter(self, query, date_from=None, date_to=None):
        if date_from:
            query = query.filter(Order.created_at >= date_from)
        if date_to:
            query = query.filter(Order.created_at <= date_to)
        return query

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
    
    # ============ ORDER METRICS ============
    
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
        approved_orders = self.db.query(Order).options(
            joinedload(Order.timeline_entries)
        ).filter(
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
        dispatched_orders = self.db.query(Order).options(
            joinedload(Order.timeline_entries)
        ).filter(
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
    
    # ============ INVENTORY METRICS ============
    
    def get_low_stock_items(self, threshold: float = None) -> list:
        """Get items below minimum quantity."""
        query = self.db.query(InventoryItem).filter(
            InventoryItem.is_active == True,
            InventoryItem.deleted_at == None,
            InventoryItem.current_quantity <= InventoryItem.minimum_quantity
        )
        return query.all()
    
    def get_inventory_health(self) -> dict:
        """Get inventory health metrics."""
        low_stock = self.get_low_stock_items()
        
        total_value = self.db.query(
            func.sum(InventoryItem.current_quantity)
        ).filter(
            InventoryItem.is_active == True,
            InventoryItem.deleted_at == None
        ).scalar() or 0
        
        return {
            "total_items": self.db.query(InventoryItem).filter(
                InventoryItem.is_active == True,
                InventoryItem.deleted_at == None
            ).count(),
            "low_stock_count": len(low_stock),
            "low_stock_items": [
                {"id": item.id, "sku": item.sku, "name": item.name, 
                 "current": float(item.current_quantity), "minimum": float(item.minimum_quantity)}
                for item in low_stock[:10]  # Top 10
            ],
            "total_quantity": float(total_value),
        }
    
    # ============ VENDOR METRICS ============
    
    def get_vendor_performance(self) -> list:
        """Get top vendors by order count."""
        vendors_data = self.db.query(
            Vendor.id,
            Vendor.name,
            func.count(Order.id).label("order_count")
        ).join(Order).filter(
            Order.deleted_at == None,
            Vendor.deleted_at == None
        ).group_by(Vendor.id, Vendor.name).order_by(
            func.count(Order.id).desc()
        ).limit(10).all()
        
        return [
            {"vendor_id": v[0], "vendor_name": v[1], "order_count": v[2]}
            for v in vendors_data
        ]
    
    def get_vendor_delivery_performance(self, vendor_id: int = None) -> dict:
        """Get vendor on-time delivery metrics."""
        query = self.db.query(Order).filter(
            Order.status.in_(["delivered", "closed"]),
            Order.deleted_at == None
        )
        
        if vendor_id:
            query = query.filter(Order.vendor_id == vendor_id)
        
        delivered_orders = query.all()
        
        if not delivered_orders:
            return {"total_delivered": 0, "on_time": 0, "late": 0, "on_time_percentage": 0}
        
        on_time = 0
        for order in delivered_orders:
            # Simple check: if delivered within 10 days of creation
            delivery_date = None
            for entry in order.timeline_entries:
                if entry.action == "delivered":
                    delivery_date = entry.created_at
                    break
            
            if delivery_date:
                days = (delivery_date - order.created_at).days
                if days <= 10:
                    on_time += 1
        
        return {
            "total_delivered": len(delivered_orders),
            "on_time": on_time,
            "late": len(delivered_orders) - on_time,
            "on_time_percentage": round((on_time / len(delivered_orders) * 100), 2) if delivered_orders else 0
        }
    
    # ============ EMAIL STATS ============
    
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
    
    # ============ USER METRICS ============
    
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
    
    # ============ DASHBOARD OVERVIEW ============
    
    def get_dashboard_overview(self, date_from=None, date_to=None) -> dict:
        period_days = 30
        if date_from and date_to:
            period_days = max(1, (date_to - date_from).days)
        return {
            "overview": {
                "total_orders": self.get_total_orders(date_from, date_to),
                "pending_approvals": self.get_pending_approvals(date_from, date_to),
                "recent_orders": self.get_recent_orders(5, date_from, date_to),
            },
            "order_metrics": self.get_order_metrics(date_from, date_to),
            "inventory_health": self.get_inventory_health(),
            "vendor_performance": self.get_vendor_performance(),
            "email_stats": self.get_email_stats(period_days),
            "user_activity": self.get_user_activity(period_days),
            "calculated_at": datetime.now(timezone.utc).isoformat(),
        }


    # ============ FILTERED DATA FOR CUSTOM REPORTS ============

    def get_filtered_orders(self, date_from=None, date_to=None, item_ids=None, vendor_ids=None):
        query = self.db.query(Order).options(
            joinedload(Order.vendor),
            selectinload(Order.items),
        ).filter(Order.deleted_at == None)
        query = self._date_filter(query, date_from, date_to)
        if vendor_ids:
            query = query.filter(Order.vendor_id.in_(vendor_ids))
        orders = query.all()
        if item_ids:
            orders = [o for o in orders if any(oi.item_id in item_ids for oi in o.items)]
        return [
            {
                "id": o.id,
                "order_number": o.order_number,
                "vendor_name": o.vendor.name if o.vendor else "",
                "status": o.status,
                "created_at": o.created_at.isoformat() if o.created_at else "",
                "item_count": len(o.items),
                "items": [
                    {"item_id": oi.item_id, "sku": oi.item.sku if oi.item else "",
                     "name": oi.item.name if oi.item else "",
                     "quantity_ordered": float(oi.quantity_ordered),
                     "quantity_dispatched": float(oi.quantity_dispatched)}
                    for oi in o.items
                ],
            }
            for o in orders
        ]

    def get_filtered_inventory(self, item_ids=None):
        query = self.db.query(InventoryItem).options(
            joinedload(InventoryItem.category),
        ).filter(
            InventoryItem.is_active == True,
            InventoryItem.deleted_at == None,
        )
        if item_ids:
            query = query.filter(InventoryItem.id.in_(item_ids))
        items = query.all()
        return [
            {
                "id": i.id, "sku": i.sku, "name": i.name,
                "current_quantity": float(i.current_quantity),
                "minimum_quantity": float(i.minimum_quantity),
                "reserved_quantity": float(i.reserved_quantity),
                "category": i.category.name if i.category else "",
            }
            for i in items
        ]


def get_analytics_service(db: Session) -> AnalyticsService:
    """Factory function to get analytics service."""
    return AnalyticsService(db)
