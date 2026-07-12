from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, selectinload, joinedload
from app.core.database import get_db
from app.core.auth import get_current_user, require_admin, require_permission
from app.models import User, Order, InventoryItem, Vendor
from app.services.analytics_service import get_analytics_service
from sqlalchemy import and_
import csv
from io import StringIO
from datetime import datetime

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard/overview")
def get_dashboard_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("dashboard.view"))
):
    """
    Get complete dashboard overview with all metrics.
    Requires dashboard.view permission (Admin and Manager roles).
    """
    analytics = get_analytics_service(db)
    return analytics.get_dashboard_overview()


@router.get("/dashboard/orders")
def get_order_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("dashboard.view"))
):
    """Get comprehensive order metrics and timing analysis. Requires dashboard.view permission."""
    analytics = get_analytics_service(db)
    return analytics.get_order_metrics()


@router.get("/dashboard/inventory")
def get_inventory_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("dashboard.view"))
):
    """Get inventory health including low stock items. Requires dashboard.view permission."""
    analytics = get_analytics_service(db)
    return analytics.get_inventory_health()


@router.get("/dashboard/vendors")
def get_vendor_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("dashboard.view"))
):
    """Get vendor performance metrics. Requires dashboard.view permission."""
    analytics = get_analytics_service(db)
    return {
        "top_vendors": analytics.get_vendor_performance(),
        "overall_delivery_performance": analytics.get_vendor_delivery_performance()
    }


@router.get("/dashboard/emails")
def get_email_stats(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("dashboard.view"))
):
    """Get email statistics for the specified period. Requires dashboard.view permission."""
    analytics = get_analytics_service(db)
    return analytics.get_email_stats(days)


@router.get("/dashboard/users")
def get_user_activity(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("dashboard.view"))
):
    """Get user activity metrics for the specified period. Requires dashboard.view permission."""
    analytics = get_analytics_service(db)
    return analytics.get_user_activity(days)


@router.post("/reports/orders/csv")
def generate_orders_report_csv(
    status: str = Query(None),
    date_from: str = Query(None),
    date_to: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Generate orders report as CSV.
    
    Query parameters:
    - status: Filter by order status (draft, approved, dispatched, etc.)
    - date_from: Start date (ISO format)
    - date_to: End date (ISO format)
    """
    query = db.query(Order).options(
        joinedload(Order.vendor),
        selectinload(Order.items),
    ).filter(Order.deleted_at == None)
    
    if status:
        query = query.filter(Order.status == status)
    
    if date_from:
        query = query.filter(Order.created_at >= datetime.fromisoformat(date_from))
    
    if date_to:
        query = query.filter(Order.created_at <= datetime.fromisoformat(date_to))
    
    orders = query.all()
    
    # Generate CSV
    output = StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow(["Order #", "Vendor", "Status", "Created", "Updated", "Items Count"])
    
    # Rows
    for order in orders:
        writer.writerow([
            order.order_number,
            order.vendor.name if order.vendor else "",
            order.status,
            order.created_at.isoformat() if order.created_at else "",
            order.updated_at.isoformat() if order.updated_at else "",
            len(order.items)
        ])
    
    csv_content = output.getvalue()
    
    return {
        "filename": f"orders_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        "content": csv_content,
        "rows": len(orders),
        "content_type": "text/csv"
    }


@router.post("/reports/inventory/csv")
def generate_inventory_report_csv(
    active_only: bool = Query(True),
    low_stock_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Generate inventory report as CSV.
    
    Query parameters:
    - active_only: Only include active items (default: true)
    - low_stock_only: Only items below minimum quantity (default: false)
    """
    query = db.query(InventoryItem).options(
        joinedload(InventoryItem.category),
    ).filter(InventoryItem.deleted_at == None)
    
    if active_only:
        query = query.filter(InventoryItem.is_active == True)
    
    items = query.all()
    
    if low_stock_only:
        items = [i for i in items if i.current_quantity <= i.minimum_quantity]
    
    # Generate CSV
    output = StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow(["SKU", "Name", "Current Qty", "Minimum Qty", "Reserved Qty", "Category", "Status"])
    
    # Rows
    for item in items:
        writer.writerow([
            item.sku,
            item.name,
            float(item.current_quantity),
            float(item.minimum_quantity),
            float(item.reserved_quantity),
            item.category.name if item.category else "",
            "Active" if item.is_active else "Inactive"
        ])
    
    csv_content = output.getvalue()
    
    return {
        "filename": f"inventory_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        "content": csv_content,
        "rows": len(items),
        "content_type": "text/csv"
    }


@router.post("/reports/vendors/csv")
def generate_vendors_report_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Generate vendor performance report as CSV."""
    vendors = db.query(Vendor).filter(Vendor.deleted_at == None).all()
    analytics = get_analytics_service(db)
    
    # Generate CSV
    output = StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow([
        "Vendor Name",
        "Contact Person",
        "Email",
        "Orders Count",
        "On-Time Delivery %",
        "Status"
    ])
    
    # Rows
    for vendor in vendors:
        perf = analytics.get_vendor_delivery_performance(vendor.id)
        writer.writerow([
            vendor.name,
            vendor.contact_person or "",
            vendor.email or "",
            len(vendor.__dict__.get("orders", [])),  # Simplified count
            perf.get("on_time_percentage", 0),
            "Active" if vendor.is_active else "Inactive"
        ])
    
    csv_content = output.getvalue()
    
    return {
        "filename": f"vendors_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        "content": csv_content,
        "rows": len(vendors),
        "content_type": "text/csv"
    }
