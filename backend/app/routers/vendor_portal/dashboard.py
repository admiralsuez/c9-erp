"""Vendor portal dashboard statistics."""

from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import Vendor, Order

from app.routers.vendor_portal.security import get_vendor_from_token, refresh_vendor_token

router = APIRouter(prefix="/vendor-portal", tags=["Vendor Portal"])

@router.get("/dashboard")
def get_vendor_dashboard(
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    """
    Get vendor dashboard with summary statistics.
    """
    vendor = get_vendor_from_token(authorization, db)
    refresh_vendor_token(vendor, db)
    
    # Get statistics
    total_orders = db.query(Order).filter(
        Order.vendor_id == vendor.id,
        Order.deleted_at == None
    ).count()
    
    pending_orders = db.query(Order).filter(
        Order.vendor_id == vendor.id,
        Order.status.in_(["pending_requisition", "signed_requisition_uploaded"]),
        Order.deleted_at == None
    ).count()
    
    approved_orders = db.query(Order).filter(
        Order.vendor_id == vendor.id,
        Order.status == "approved",
        Order.deleted_at == None
    ).count()
    
    dispatched_orders = db.query(Order).filter(
        Order.vendor_id == vendor.id,
        Order.status == "dispatched",
        Order.deleted_at == None
    ).count()
    
    delivered_orders = db.query(Order).filter(
        Order.vendor_id == vendor.id,
        Order.status == "delivered",
        Order.deleted_at == None
    ).count()
    
    # Get recent orders
    recent_orders = db.query(Order).filter(
        Order.vendor_id == vendor.id,
        Order.deleted_at == None
    ).order_by(Order.created_at.desc()).limit(5).all()
    
    return {
        "vendor_id": vendor.id,
        "vendor_name": vendor.name,
        "contact_person": vendor.contact_person,
        "email": vendor.email,
        "statistics": {
            "total_orders": total_orders,
            "pending_orders": pending_orders,
            "approved_orders": approved_orders,
            "dispatched_orders": dispatched_orders,
            "delivered_orders": delivered_orders
        },
        "recent_orders": recent_orders
    }
