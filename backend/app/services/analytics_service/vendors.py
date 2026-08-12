"""Analytics service with pre-built queries for dashboards and reporting."""

import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import func, and_, or_

from app.models import Order, OrderItem, InventoryItem, Vendor, User, EmailLog, AuditLog

logger = logging.getLogger(__name__)


class VendorMetricsMixin:
    """Vendor performance and delivery metrics."""

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
        try:
            query = self.db.query(Order).options(
                joinedload(Order.timeline_entries)
            ).filter(
                Order.status.in_(["delivered", "closed"]),
                Order.deleted_at == None
            )
            
            if vendor_id:
                query = query.filter(Order.vendor_id == vendor_id)
            
            delivered_orders = query.all()
        except Exception:
            # Fallback to lazy load
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
