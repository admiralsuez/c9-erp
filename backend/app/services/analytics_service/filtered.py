"""Analytics service with pre-built queries for dashboards and reporting."""

import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import func, and_, or_

from app.models import Order, OrderItem, InventoryItem, Vendor, User, EmailLog, AuditLog

logger = logging.getLogger(__name__)


class FilteredDataMixin:
    """Filtered data queries for custom reports."""

    def get_filtered_orders(self, date_from=None, date_to=None, item_ids=None, vendor_ids=None, page: int = 1, page_size: int = 50):
        """Get filtered orders with pagination support."""
        query = self.db.query(Order).options(
            joinedload(Order.vendor),
            selectinload(Order.items),
        ).filter(Order.deleted_at == None)
        query = self._date_filter(query, date_from, date_to)
        if vendor_ids:
            query = query.filter(Order.vendor_id.in_(vendor_ids))
        
        # Get total count before pagination
        all_orders = query.all()
        if item_ids:
            all_orders = [o for o in all_orders if any(oi.item_id in item_ids for oi in o.items)]
        
        total_count = len(all_orders)
        total_pages = (total_count + page_size - 1) // page_size
        
        # Apply pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_orders = all_orders[start_idx:end_idx]
        
        return {
            "data": [
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
                for o in paginated_orders
            ],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_count": total_count,
                "total_pages": total_pages,
            }
        }

    def get_filtered_inventory(self, item_ids=None, page: int = 1, page_size: int = 50):
        """Get filtered inventory with pagination support."""
        query = self.db.query(InventoryItem).options(
            joinedload(InventoryItem.category),
        ).filter(
            InventoryItem.is_active == True,
            InventoryItem.deleted_at == None,
        )
        if item_ids:
            query = query.filter(InventoryItem.id.in_(item_ids))
        
        # Get total count
        total_count = query.count()
        total_pages = (total_count + page_size - 1) // page_size
        
        # Apply pagination
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        
        return {
            "data": [
                {
                    "id": i.id, "sku": i.sku, "name": i.name,
                    "current_quantity": float(i.current_quantity),
                    "minimum_quantity": float(i.minimum_quantity),
                    "reserved_quantity": float(i.reserved_quantity),
                    "category": i.category.name if i.category else "",
                }
                for i in items
            ],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_count": total_count,
                "total_pages": total_pages,
            }
        }
