import logging
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.auth import get_current_user, require_permission
from app.core.database import get_db
from app.models import InventoryItem, Order, OrderItem, SerialNumber, User, Vendor
from app.schemas import InventoryItemResponse, OrderCreateRequest, OrderResponse, OrderUpdateRequest
from app.services.serial_number_service import serial_number_service
from app.services.query_optimizer import optimize_order_query

from .orders_common import OrderStatus, add_timeline_entry, generate_order_number, reserve_stock

router = APIRouter(prefix="/orders", tags=["Orders"])
logger = logging.getLogger(__name__)

@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    order_data: OrderCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("orders.create"))
):
    """Create a new order in Draft status."""
    # Verify vendor exists
    vendor = db.query(Vendor).filter(
        Vendor.id == order_data.vendor_id,
        Vendor.deleted_at == None
    ).first()
    
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    # Verify all items exist (exclude parent items — only orderable variants)
    item_ids = [item.item_id for item in order_data.items]
    items = db.query(InventoryItem).options(
        selectinload(InventoryItem.serial_numbers)
    ).filter(InventoryItem.id.in_(item_ids), InventoryItem.deleted_at == None).all()
    
    if len(items) != len(item_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more items not found"
        )
    
    # Validate serials: for each item, check serials if provided
    for item_data in order_data.items:
        item = next((i for i in items if i.id == item_data.item_id), None)
        if not item:
            continue
        # Parent items cannot be ordered directly
        item_children = db.query(InventoryItem).filter(
            InventoryItem.parent_id == item.id,
            InventoryItem.deleted_at == None
        ).count()
        if item_children > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Item '{item.name}' is a parent product and cannot be ordered directly. Select a variant instead."
            )
        # If serial_ids provided, validate count and assignment
        if item_data.serial_ids:
            if len(item_data.serial_ids) != int(item_data.quantity_ordered):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Item '{item.name}': number of serials ({len(item_data.serial_ids)}) must match quantity ({int(item_data.quantity_ordered)})"
                )
            serials = db.query(SerialNumber).filter(
                SerialNumber.id.in_(item_data.serial_ids),
                SerialNumber.item_id == item.id,
                SerialNumber.assigned_to_order_id == None
            ).all()
            if len(serials) != len(item_data.serial_ids):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"One or more serials for '{item.name}' are already assigned or don't belong to this item"
                )
    
    # Validate backdate if provided
    order_created_at = datetime.now(timezone.utc)
    if order_data.order_date:
        from datetime import timedelta
        try:
            # If order_date is a string (ISO format from frontend), parse it
            if isinstance(order_data.order_date, str):
                backdate = datetime.fromisoformat(order_data.order_date.replace('Z', '+00:00'))
            else:
                backdate = order_data.order_date
            
            # Ensure we're comparing UTC datetimes
            if backdate.tzinfo is None:
                backdate = backdate.replace(tzinfo=timezone.utc)
            
            # Validate backdate is not in the future
            if backdate > order_created_at:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Order date cannot be in the future"
                )
            # Validate backdate is not more than 30 days in the past
            if order_created_at - backdate > timedelta(days=30):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Order date cannot be more than 30 days in the past"
                )
            order_created_at = backdate
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid order date format: {str(e)}. Expected ISO format (YYYY-MM-DD)"
            )
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            order_number = generate_order_number(db, "ORD-{YYYY}-{SEQ}", current_user.location or "HO", attempt, order_created_at)

            # Create order
            order = Order(
                order_number=order_number,
                vendor_id=order_data.vendor_id,
                status=OrderStatus.DRAFT,
                remarks=order_data.remarks,
                delivery_address=order_data.delivery_address,
                created_by=current_user.id,
                created_at=order_created_at  # Use backdate if provided
            )
            db.add(order)
            db.flush()

            # Add items and assign serials
            for item_data in order_data.items:
                order_item = OrderItem(
                    order_id=order.id,
                    item_id=item_data.item_id,
                    quantity_ordered=Decimal(str(item_data.quantity_ordered))
                )
                db.add(order_item)
                db.flush()

                # Assign serials to order if provided
                if item_data.serial_ids:
                    for sid in item_data.serial_ids:
                        serial_number_service.assign_to_order(db, sid, order.id)

            # Add timeline entry
            add_timeline_entry(db, order, "created", current_user)
            
            # Reserve stock immediately on creation
            db.flush()
            reserve_stock(db, order, current_user)
            
            db.commit()
            db.refresh(order)
            break
        except IntegrityError:
            db.rollback()
            if attempt == max_retries - 1:
                raise HTTPException(status_code=500, detail="Failed to generate unique order number. Please retry.")
            continue
    return order
@router.get("")
def list_orders(
    status: str = Query(None),
    status_not: str = Query(None),
    vendor_id: int = Query(None),
    search: str = Query(None),
    date_from: str = Query(None),
    date_to: str = Query(None),
    sort_by: str = Query("recent_activity", pattern="^(recent_activity|created_date)$"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List orders with filtering and sorting. Returns paginated response."""
    query = db.query(Order).filter(Order.deleted_at == None)
    
    if status:
        query = query.filter(Order.status == status)
    
    if status_not:
        excluded = [s.strip() for s in status_not.split(",")]
        query = query.filter(~Order.status.in_(excluded))
    if vendor_id:
        query = query.filter(Order.vendor_id == vendor_id)
    
    if search:
        query = query.filter(
            or_(
                Order.order_number.ilike(f"%{search}%"),
                Order.remarks.ilike(f"%{search}%")
            )
        )
    
    if date_from:
        from datetime import datetime
        dt_from = datetime.strptime(date_from, "%Y-%m-%d")
        query = query.filter(Order.created_at >= dt_from)
    
    if date_to:
        from datetime import datetime, timedelta
        dt_to = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
        query = query.filter(Order.created_at < dt_to)
    
    # Apply sorting
    if sort_by == "recent_activity":
        # Most recent activity (updated_at descending, then created_at)
        query = query.order_by(desc(Order.updated_at), desc(Order.created_at))
    else:  # created_date
        # Most recently created first
        query = query.order_by(desc(Order.created_at))
    
    try:
        total = query.count()
    except Exception as e:
        logger.error(f"Error counting orders: {e}")
        return {
            "items": [],
            "total": 0,
            "page": page,
            "size": size,
            "pages": 0,
            "error": "Failed to count orders"
        }
    
    skip = (page - 1) * size
    try:
        orders = optimize_order_query(query).offset(skip).limit(size).all()
    except Exception as e:
        logger.error(f"Error fetching orders: {e}")
        return {
            "items": [],
            "total": total,
            "page": page,
            "size": size,
            "pages": 0,
            "error": "Failed to fetch orders"
        }
    
    total_pages = (total + size - 1) // size
    
    # Serialize orders safely
    try:
        orders_data = []
        for order in orders:
            try:
                orders_data.append(OrderResponse.model_validate(order))
            except Exception as e:
                logger.error(f"Error validating order {order.id}: {e}")
                # Skip orders that fail validation
                continue
    except Exception as e:
        logger.error(f"Error serializing orders: {e}")
        orders_data = []
    
    return {
        "items": orders_data,
        "total": total,
        "page": page,
        "size": size,
        "pages": total_pages
    }
@router.get("/available-items")
def list_available_items(
    category_id: int = Query(None),
    search: str = Query(None),
    attributes: str = Query(None, description="JSON filter e.g. {\"usage\": \"events_only\"}"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List available items for order placement, including attributes for filtering."""
    try:
        query = db.query(InventoryItem).options(
            selectinload(InventoryItem.attributes),
        ).filter(
            InventoryItem.deleted_at == None,
            InventoryItem.is_active == True,
            InventoryItem.is_container == False,  # Only sellable items
        )

        if category_id:
            query = query.filter(InventoryItem.category_id == category_id)

        if search:
            query = query.filter(
                or_(
                    InventoryItem.name.ilike(f"%{search}%"),
                    InventoryItem.sku.ilike(f"%{search}%"),
                    InventoryItem.barcode.ilike(f"%{search}%"),
                )
            )

        items = query.all()
    except Exception as e:
        logger.error(f"Error fetching available items: {e}")
        return []

    # Filter by attributes if specified
    if attributes:
        import json
        try:
            attr_filter = json.loads(attributes)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid attributes filter JSON")
        filtered = []
        for item in items:
            try:
                item_attrs = {a.attribute_name: a.attribute_value for a in (item.attributes or [])}
                if all(item_attrs.get(k) == v for k, v in attr_filter.items()):
                    filtered.append(item)
            except Exception as e:
                logger.error(f"Error filtering item {item.id}: {e}")
                # Skip items that fail filtering
                continue
        items = filtered

    # Serialize items safely
    try:
        result = []
        for item in items:
            try:
                result.append(InventoryItemResponse.model_validate(item))
            except Exception as e:
                logger.error(f"Error validating item {item.id}: {e}")
                # Skip items that fail validation
                continue
        return result
    except Exception as e:
        logger.error(f"Error serializing available items: {e}")
        return []
@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get order details."""
    order = db.query(Order).options(
        selectinload(Order.items).selectinload(OrderItem.item),
        selectinload(Order.timeline_entries),
        selectinload(Order.vendor),
    ).filter(
        Order.id == order_id,
        Order.deleted_at == None
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return order
@router.patch("/{order_id}", response_model=OrderResponse)
def update_order(
    order_id: int,
    order_data: OrderUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("orders.create"))
):
    """Update order (only in Draft or Pending Requisition status)."""
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.deleted_at == None
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Only allow edits in Draft or Pending Requisition
    if order.status not in [OrderStatus.DRAFT, OrderStatus.PENDING_REQUISITION]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot edit order in {order.status} status"
        )
    
    # Update basic fields
    if order_data.remarks is not None:
        order.remarks = order_data.remarks
    if order_data.delivery_address is not None:
        order.delivery_address = order_data.delivery_address
    
    # Update vendor and items only if not yet signed
    if order.status in [OrderStatus.DRAFT, OrderStatus.PENDING_REQUISITION]:
        if order_data.vendor_id is not None:
            vendor = db.query(Vendor).filter(Vendor.id == order_data.vendor_id).first()
            if not vendor:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Vendor not found"
                )
            order.vendor_id = order_data.vendor_id
        
        if order_data.items is not None:
            # Delete old items and add new ones
            for item in order.items:
                db.delete(item)
            
            for item_data in order_data.items:
                order_item = OrderItem(
                    order_id=order.id,
                    item_id=item_data.item_id,
                    quantity_ordered=Decimal(str(item_data.quantity_ordered))
                )
                db.add(order_item)
    
    db.commit()
    db.refresh(order)
    return order
