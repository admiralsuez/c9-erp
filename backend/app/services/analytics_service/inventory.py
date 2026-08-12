"""Analytics service with pre-built queries for dashboards and reporting."""

import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import func, and_, or_

from app.models import Order, OrderItem, InventoryItem, Vendor, User, EmailLog, AuditLog

logger = logging.getLogger(__name__)


class InventoryMetricsMixin:
    """Inventory health and low-stock metrics."""

    def get_low_stock_items(self, threshold: float = None) -> list:
        """Get items below minimum quantity (excludes containers, uses available qty)."""
        from app.models import Settings
        if threshold is None:
            global_setting = self.db.query(Settings).first()
            threshold = float(global_setting.default_low_stock_threshold) if global_setting and global_setting.default_low_stock_threshold else 10

        q = self.db.query(InventoryItem).filter(
            InventoryItem.is_active == True,
            InventoryItem.deleted_at == None,
            InventoryItem.is_container == False,
        )

        items = q.all()

        result = []
        for item in items:
            available = float(item.current_quantity - item.reserved_quantity)
            min_qty = float(item.minimum_quantity) if item.minimum_quantity and item.minimum_quantity > 0 else threshold
            if available < min_qty:
                result.append(item)
        return result

    def get_inventory_health(self) -> dict:
        """Get inventory health metrics (excludes containers)."""
        base_filter = [
            InventoryItem.is_active == True,
            InventoryItem.deleted_at == None,
            InventoryItem.is_container == False,
        ]

        low_stock = self.get_low_stock_items()
        
        total_value = self.db.query(
            func.sum(InventoryItem.current_quantity)
        ).filter(*base_filter).scalar() or 0
        
        return {
            "total_items": self.db.query(InventoryItem).filter(*base_filter).count(),
            "low_stock_count": len(low_stock),
            "low_stock_items": [
                {
                    "id": item.id, "sku": item.sku, "name": item.name,
                    "current": float(item.current_quantity),
                    "reserved": float(item.reserved_quantity),
                    "available": float(item.current_quantity - item.reserved_quantity),
                    "minimum": float(item.minimum_quantity),
                }
                for item in low_stock[:10]  # Top 10
            ],
            "total_quantity": float(total_value),
        }
