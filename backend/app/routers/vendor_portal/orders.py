"""Vendor portal order views and document downloads."""

from fastapi import APIRouter, Depends, HTTPException, Header, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import Vendor, Order, Document
from typing import Optional
from datetime import datetime
from app.services.storage import get_storage_backend

from app.routers.vendor_portal.security import get_vendor_from_token, refresh_vendor_token

router = APIRouter(prefix="/vendor-portal", tags=["Vendor Portal"])

@router.get("/orders")
def list_vendor_orders(
    authorization: str = Header(...),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List all orders for a vendor (read-only access).
    Returns open and recent orders.
    """
    vendor = get_vendor_from_token(authorization, db)
    refresh_vendor_token(vendor, db)
    
    query = db.query(Order).filter(
        Order.vendor_id == vendor.id,
        Order.deleted_at == None
    )
    
    if status:
        query = query.filter(Order.status == status)
    
    # Order by most recent first
    query = query.order_by(Order.created_at.desc())
    
    skip = (page - 1) * size
    orders = query.offset(skip).limit(size).all()
    
    return {
        "vendor_id": vendor.id,
        "vendor_name": vendor.name,
        "orders": orders,
        "page": page,
        "page_size": size,
        "total": query.count()
    }

@router.get("/orders/{order_id}")
def get_vendor_order(
    order_id: int,
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific order.
    Vendor can only access their own orders.
    """
    vendor = get_vendor_from_token(authorization, db)
    refresh_vendor_token(vendor, db)
    
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.vendor_id == vendor.id,
        Order.deleted_at == None
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Prepare response with order details and timeline
    return {
        "order": order,
        "timeline": order.timeline_entries,
        "items": order.items,
        "documents": db.query(Document).filter(
            Document.order_id == order_id,
            Document.version_status.in_(["current"])
        ).all()
    }

@router.get("/orders/{order_id}/download/{document_id}")
def download_order_document(
    order_id: int,
    document_id: int,
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    """
    Download a document associated with an order.
    Vendor can only download documents from their own orders.
    """
    vendor = get_vendor_from_token(authorization, db)
    refresh_vendor_token(vendor, db)
    
    # Verify order belongs to vendor
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.vendor_id == vendor.id,
        Order.deleted_at == None
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Get document
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.order_id == order_id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Read file from storage
    storage = get_storage_backend()
    file_content = storage.read(document.storage_path)
    
    if not file_content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found in storage"
        )
    
    return {
        "file_name": document.file_name,
        "file_type": document.file_type,
        "content": file_content,
        "size": len(file_content)
    }

@router.post("/search-orders")
def search_vendor_orders(
    authorization: str = Header(...),
    order_number: Optional[str] = None,
    status: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Search vendor orders with filters.
    """
    vendor = get_vendor_from_token(authorization, db)
    refresh_vendor_token(vendor, db)
    
    query = db.query(Order).filter(
        Order.vendor_id == vendor.id,
        Order.deleted_at == None
    )
    
    if order_number:
        query = query.filter(Order.order_number.ilike(f"%{order_number}%"))
    
    if status:
        query = query.filter(Order.status == status)
    
    if from_date:
        try:
            from_datetime = datetime.fromisoformat(from_date)
            query = query.filter(Order.created_at >= from_datetime)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid from_date format. Use ISO format (YYYY-MM-DD)"
            )
    
    if to_date:
        try:
            to_datetime = datetime.fromisoformat(to_date)
            query = query.filter(Order.created_at <= to_datetime)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid to_date format. Use ISO format (YYYY-MM-DD)"
            )
    
    orders = query.order_by(Order.created_at.desc()).all()
    
    return {
        "vendor_id": vendor.id,
        "vendor_name": vendor.name,
        "search_results": orders,
        "count": len(orders)
    }
