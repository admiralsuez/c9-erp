import logging
from decimal import Decimal
from typing import List

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.auth import get_current_user, require_admin, require_permission
from app.core.database import get_db
from app.models import (
    Document,
    InventoryItem,
    InventoryTransaction,
    Notification,
    Order,
    OrderItem,
    OrderTimeline,
    SerialNumber,
    Settings,
    User,
    Vendor,
)
from app.schemas import (
    DispatchRequestBody,
    OrderItemResponse,
    OrderResponse,
    OrderTimelineEntryResponse,
    ReturnOrderRequest,
)
from app.services.audit_service import log_audit
from app.services.order_email_helper import (
    send_order_approved_email,
    send_order_cancelled_email,
    send_order_delivered_email,
    send_order_dispatched_email,
)
from app.services.pdf_generator import PDFGenerator
from app.services.serial_number_service import serial_number_service
from app.services.storage import get_storage_backend

from .orders_common import (
    OrderStatus,
    add_timeline_entry,
    dispatch_stock,
    evaluate_approval_matrix,
    release_reservation,
)

router = APIRouter(prefix="/orders", tags=["Orders"])
logger = logging.getLogger(__name__)

@router.post("/{order_id}/approve", response_model=OrderResponse)
def approve_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Signed -> Approved (with approval matrix check and reservation)."""
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.deleted_at == None
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if order.status != OrderStatus.SIGNED_REQUISITION_UPLOADED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve order in {order.status} status"
        )
    
    # Check approval matrix
    evaluate_approval_matrix(db, order, current_user)
    
    # Stock already reserved at order creation — no additional reservation needed
    
    order.status = OrderStatus.APPROVED
    add_timeline_entry(db, order, "approved", current_user)
    log_audit(db, user_id=current_user.id, action="order.approved", entity_type="order", entity_id=order.id)
    db.commit()
    db.refresh(order)
    
    # Send order approved email (non-blocking)
    try:
        send_order_approved_email(db, order, current_user.full_name)
    except Exception as e:
        logger.warning("Email send failed for order %s: %s", order.id, str(e))
    
    return order
@router.post("/{order_id}/approve-with-signature", response_model=OrderResponse)
def approve_with_signature(
    order_id: int,
    body: dict = Body(..., embed=False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    signature_data = body.get("signature_data", "")
    """Approve order with e-signature. Auto-generates signed PDF."""
    order = db.query(Order).options(
        selectinload(Order.items).selectinload(OrderItem.item),
        joinedload(Order.vendor),
    ).filter(
        Order.id == order_id,
        Order.deleted_at == None
    ).first()
    
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    
    # Check approval matrix (evaluates rules, fallback to orders.approve permission)
    evaluate_approval_matrix(db, order, current_user)
    
    if order.status != OrderStatus.PENDING_REQUISITION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve order in {order.status} status"
        )
    
    # Generate signed PDF
    try:
        company_settings = db.query(Settings).first()
        settings_dict = {
            "company_name": company_settings.company_name if company_settings else "Cloud9",
            "company_address": company_settings.company_address if company_settings else "",
            "header_text": company_settings.pdf_header_text if company_settings else "",
            "footer_text": company_settings.pdf_footer_text if company_settings else ""
        }
        
        pdf_items = []
        for order_item in order.items:
            pdf_items.append({
                "sku": order_item.item.sku,
                "name": order_item.item.name,
                "quantity": str(order_item.quantity_ordered),
                "description": order_item.item.description or ""
            })
        
        creator = db.query(User).filter(User.id == order.created_by).first()
        
        pdf_gen = PDFGenerator(
            company_name=settings_dict.get("company_name", "Cloud9")
        )
        
        pdf_content = pdf_gen.generate_requisition(
            order_number=order.order_number,
            vendor_name=order.vendor.name,
            vendor_address=order.vendor.address or "",
            items=pdf_items,
            remarks=order.remarks or "",
            delivery_address=order.delivery_address or "",
            requested_by=creator.full_name if creator else "Unknown",
            company_address=settings_dict.get("company_address", ""),
            order_url=f"/orders/{order.id}",
            header_text=settings_dict.get("header_text", ""),
            footer_text=settings_dict.get("footer_text", ""),
            approver_name=current_user.full_name or current_user.email,
            approver_signature_base64=signature_data
        )
        
        # Save signed PDF
        storage = get_storage_backend()
        storage_path = storage.save(
            f"orders/{order.id}/signed_requisition_{order.order_number}.pdf",
            pdf_content
        )
        
        # Supersede previous requisition documents
        previous_docs = db.query(Document).filter(
            Document.order_id == order.id,
            Document.doc_category.in_(["requisition", "signed_requisition"]),
            Document.version_status == "current"
        ).all()
        
        max_version = 0
        for pd in previous_docs:
            pd.version_status = "superseded"
            if pd.version and pd.version > max_version:
                max_version = pd.version
        
        # Create signed document record
        signed_doc = Document(
            order_id=order.id,
            file_name=f"signed_requisition_{order.order_number}.pdf",
            file_type="pdf",
            storage_path=storage_path,
            doc_category="signed_requisition",
            version=max_version + 1,
            version_status="current",
            notes=f"Auto-generated signed PDF approved by {current_user.full_name or current_user.email}",
            uploaded_by=current_user.id
        )
        db.add(signed_doc)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Signed PDF generation failed: {str(e)}"
        )
    
    # Stock already reserved at order creation
    
    # Update status
    order.status = OrderStatus.APPROVED
    add_timeline_entry(
        db, order, "approved",
        current_user,
        comments=f"Approved with e-signature by {current_user.full_name or current_user.email}"
    )
    db.flush()
    
    # Mark approval notification as read
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.related_entity_type == "order",
        Notification.related_entity_id == order.id,
        Notification.type == "approval_required"
    ).update({"is_read": True})
    
    # Notify creator that order was approved
    if order.approver_id and order.created_by and order.created_by != current_user.id:
        notify = Notification(
            user_id=order.created_by,
            actor_id=current_user.id,
            title="Requisition Approved",
            message=f"Your requisition {order.order_number} has been approved.",
            type="approved",
            related_entity_type="order",
            related_entity_id=order.id,
            is_read=False
        )
        db.add(notify)
    
    log_audit(db, user_id=current_user.id, action="order.approved", entity_type="order", entity_id=order.id)
    
    db.commit()
    db.refresh(order)
    
    try:
        send_order_approved_email(db, order, current_user.full_name)
    except Exception as e:
        logger.warning("Email send failed for order %s: %s", order.id, str(e))
    
    return order
@router.post("/{order_id}/dispatch", response_model=OrderResponse)
def dispatch_order(
    order_id: int,
    dispatch_data: DispatchRequestBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("inventory.dispatch"))
):
    """Approved -> Dispatched (with ledger updates)."""
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.deleted_at == None
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if order.status != OrderStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot dispatch order in {order.status} status"
        )
    
    # Dispatch stock with ledger entries
    dispatch_errors = dispatch_stock(db, order, dispatch_data.items, current_user, dispatch_data.partial)
    if dispatch_errors and not dispatch_data.partial:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": "Cannot dispatch order", "errors": dispatch_errors}
        )
    
    order.status = OrderStatus.DISPATCHED
    add_timeline_entry(db, order, "dispatched", current_user)
    log_audit(db, user_id=current_user.id, action="order.dispatched", entity_type="order", entity_id=order.id)
    db.commit()
    db.refresh(order)
    
    # Send order dispatched email (non-blocking)
    try:
        send_order_dispatched_email(db, order)
    except Exception as e:
        logger.warning("Email send failed for order %s: %s", order.id, str(e))
    
    return order


@router.post("/{order_id}/deliver", response_model=OrderResponse)
def mark_delivered(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Dispatched -> Delivered."""
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.deleted_at == None
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if order.status != OrderStatus.DISPATCHED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot mark delivered from {order.status} status"
        )
    
    order.status = OrderStatus.DELIVERED
    add_timeline_entry(db, order, "delivered", current_user)
    db.commit()
    db.refresh(order)
    
    # Send order delivered email (non-blocking)
    try:
        send_order_delivered_email(db, order)
    except Exception as e:
        logger.warning("Email send failed for order %s: %s", order.id, str(e))
    
    log_audit(db, user_id=current_user.id, action="order.delivered", entity_type="order", entity_id=order.id)
    db.commit()
    return order
@router.post("/{order_id}/close", response_model=OrderResponse)
def close_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delivered -> Closed."""
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.deleted_at == None
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if order.status != OrderStatus.DELIVERED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot close order from {order.status} status"
        )
    
    order.status = OrderStatus.CLOSED
    add_timeline_entry(db, order, "closed", current_user)
    log_audit(db, user_id=current_user.id, action="order.closed", entity_type="order", entity_id=order.id)
    db.commit()
    db.refresh(order)
    return order
@router.post("/{order_id}/cancel", response_model=OrderResponse)
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Any non-terminal -> Cancelled (releases reservation)."""
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.deleted_at == None
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if order.status in [OrderStatus.CLOSED, OrderStatus.CANCELLED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel order in {order.status} status"
        )
    
    # Release reservation (stock is reserved from creation onwards)
    if any(oi.quantity_reserved > 0 for oi in order.items):
        release_reservation(db, order)
    
    # Release serials
    assigned_serials = db.query(SerialNumber).filter(
        SerialNumber.assigned_to_order_id == order.id
    ).all()
    for s in assigned_serials:
        serial_number_service.unassign_from_order(db, s.id)
    
    order.status = OrderStatus.CANCELLED
    add_timeline_entry(db, order, "cancelled", current_user)
    log_audit(db, user_id=current_user.id, action="order.cancelled", entity_type="order", entity_id=order.id)
    db.commit()
    db.refresh(order)
    
    # Send order cancelled email (non-blocking)
    try:
        send_order_cancelled_email(db, order, "", current_user.full_name)
    except Exception as e:
        logger.warning("Email send failed for order %s: %s", order.id, str(e))
    
    return order
@router.post("/{order_id}/reopen", response_model=OrderResponse)
def reopen_order(
    order_id: int,
    reason: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Approved -> Draft (Admin only, requires reason)."""
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.deleted_at == None
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if order.status != OrderStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Can only reopen orders in {OrderStatus.APPROVED} status"
        )
    
    # Release reservation
    release_reservation(db, order)
    
    order.status = OrderStatus.DRAFT
    add_timeline_entry(db, order, "reopened", current_user, reason)
    log_audit(db, user_id=current_user.id, action="order.reopened", entity_type="order", entity_id=order.id)
    db.commit()
    db.refresh(order)
    return order
@router.post("/{order_id}/return", response_model=OrderResponse)
def return_order(
    order_id: int,
    body: ReturnOrderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Return items from a closed order with per-item quantities, damaged tracking, and photos."""
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.deleted_at == None
    ).options(
        selectinload(Order.items).selectinload(OrderItem.item),
    ).first()

    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if order.status != OrderStatus.CLOSED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Can only return items from closed orders")
    if not body.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No return items provided")

    from app.services.inventory_service import _lock_items

    oi_map = {oi.id: oi for oi in order.items}
    item_ids = list(set(r.item_id for r in body.items))
    locked = _lock_items(db, item_ids)

    total_returned = 0
    for ret in body.items:
        oi = oi_map.get(ret.order_item_id)
        if not oi:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Order item #{ret.order_item_id} not found")
        if not oi.item or oi.item.item_type not in ["returnable", "consumable"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Item #{oi.item_id} cannot be returned (only returnable and consumable items are eligible)")
        if ret.quantity_returned <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Return quantity must be positive")
        if ret.quantity_damaged < 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Damaged quantity cannot be negative")
        if ret.quantity_damaged > ret.quantity_returned:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Damaged quantity cannot exceed returned quantity")

        remaining = oi.quantity_dispatched - oi.quantity_returned
        if ret.quantity_returned > remaining:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Item #{oi.item_id}: only {remaining} units left to return (dispatched: {oi.quantity_dispatched}, already returned: {oi.quantity_returned})"
            )

        item = locked.get(oi.item_id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Inventory item #{oi.item_id} not found")

        good_qty = Decimal(str(ret.quantity_returned - ret.quantity_damaged))
        if good_qty > 0:
            previous_qty = item.current_quantity
            new_qty = previous_qty + good_qty
            transaction = InventoryTransaction(
                item_id=item.id,
                transaction_type="return",
                previous_quantity=previous_qty,
                change_quantity=good_qty,
                new_quantity=new_qty,
                reference_type="return",
                reference_id=order.id,
                reason=f"Return from order {order.order_number} - {ret.reason or ''}".strip(),
                created_by=current_user.id,
            )
            db.add(transaction)
            item.current_quantity = new_qty

        oi.quantity_returned += Decimal(str(ret.quantity_returned))
        oi.quantity_damaged += Decimal(str(ret.quantity_damaged))
        total_returned += ret.quantity_returned

    add_timeline_entry(db, order, "returned", current_user, f"Returned {total_returned} unit(s)")
    log_audit(db, user_id=current_user.id, action="order.returned", entity_type="order", entity_id=order.id)
    db.commit()
    db.refresh(order)
    return order
@router.post("/{order_id}/items/{order_item_id}/return-reason")
def set_order_item_return_reason(
    order_id: int,
    order_item_id: int,
    body: dict = Body(..., embed=False),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("orders.manage"))
):
    """Set return reason for a consumable order item (damaged or not_needed)."""
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.deleted_at == None
    ).first()
    
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    
    order_item = db.query(OrderItem).filter(
        OrderItem.id == order_item_id,
        OrderItem.order_id == order_id
    ).first()
    
    if not order_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order item not found")
    
    # Get inventory item to check if consumable
    item = db.query(InventoryItem).filter(InventoryItem.id == order_item.item_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory item not found")
    
    # Validate return reason
    return_reason = body.get("return_reason", "")
    if return_reason not in ["damaged", "not_needed"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="return_reason must be 'damaged' or 'not_needed'"
        )
    
    # Update return reason and status
    order_item.return_reason = return_reason
    order_item.return_status = "pending"  # Mark as pending return
    
    db.commit()
    db.refresh(order_item)
    
    return OrderItemResponse.model_validate(order_item)
@router.get("/{order_id}/timeline", response_model=List[OrderTimelineEntryResponse])
def get_order_timeline(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get order timeline (immutable)."""
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.deleted_at == None
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return order.timeline_entries
