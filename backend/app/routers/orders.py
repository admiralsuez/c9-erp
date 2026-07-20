from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy import and_, or_, func, desc
from sqlalchemy.exc import IntegrityError
from app.core.database import get_db
from app.core.auth import get_current_user, require_permission, require_admin
from app.models import (
    User, Order, OrderItem, OrderTimeline, InventoryItem,
    InventoryTransaction, Vendor, ApprovalRule, Role, Document, Settings, Notification,
    SerialNumber
)
from app.services.serial_number_service import serial_number_service
from app.services.audit_service import log_audit
from app.services.inventory_service import reserve_stock as svc_reserve, release_reservation as svc_release, dispatch_stock as svc_dispatch
from app.schemas import (
    OrderCreateRequest, OrderUpdateRequest, OrderResponse, OrderItemResponse,
    DispatchRequestBody, ApprovalRuleCreateRequest, ApprovalRuleResponse,
    OrderTimelineEntryResponse, ReturnOrderRequest,
)
from typing import List
from decimal import Decimal
from datetime import datetime, timezone
from enum import Enum
import os
import re
import logging
from app.services.pdf_generator import PDFGenerator

logger = logging.getLogger(__name__)
from app.services.storage import get_storage_backend
from app.services.order_email_helper import (
    send_requisition_created_email,
    send_order_approved_email,
    send_order_dispatched_email,
    send_order_delivered_email,
    send_order_cancelled_email
)

router = APIRouter(prefix="/orders", tags=["Orders"])


# ============ ORDER STATE MACHINE ============
class OrderStatus(str, Enum):
    DRAFT = "draft"
    PENDING_REQUISITION = "pending_requisition"
    SIGNED_REQUISITION_UPLOADED = "signed_requisition_uploaded"
    APPROVED = "approved"
    DISPATCHED = "dispatched"
    DELIVERED = "delivered"
    CLOSED = "closed"
    CANCELLED = "cancelled"


# Valid state transitions
VALID_TRANSITIONS = {
    OrderStatus.DRAFT: [OrderStatus.PENDING_REQUISITION, OrderStatus.CANCELLED],
    OrderStatus.PENDING_REQUISITION: [OrderStatus.SIGNED_REQUISITION_UPLOADED, OrderStatus.CANCELLED, OrderStatus.DRAFT],
    OrderStatus.SIGNED_REQUISITION_UPLOADED: [OrderStatus.APPROVED, OrderStatus.CANCELLED, OrderStatus.DRAFT],
    OrderStatus.APPROVED: [OrderStatus.DISPATCHED, OrderStatus.CANCELLED, OrderStatus.DRAFT],
    OrderStatus.DISPATCHED: [OrderStatus.DELIVERED, OrderStatus.CANCELLED],
    OrderStatus.DELIVERED: [OrderStatus.CLOSED],
    OrderStatus.CLOSED: [],
    OrderStatus.CANCELLED: [],
}


def generate_order_number(db: Session, settings_format: str, location: str = "HO") -> str:
    """Generate unique order number using settings format with location prefix."""
    year = datetime.now(timezone.utc).year
    
    settings = db.query(Settings).first()
    prefix = (settings.llf_prefix if location == "LLF" else settings.ho_prefix) if settings else ("LLF" if location == "LLF" else "HO")
    
    count = db.query(func.count(Order.id)).filter(
        func.extract('year', Order.created_at) == year,
        Order.deleted_at == None
    ).scalar() or 0
    seq = count + 1
    
    return f"{prefix}-ORD-{year}-{seq:06d}"


def add_timeline_entry(db: Session, order: Order, action: str, user: User, comments: str = None):
    """Add immutable entry to order timeline."""
    entry = OrderTimeline(
        order_id=order.id,
        action=action,
        comments=comments,
        user_id=user.id
    )
    db.add(entry)


# ============ APPROVAL MATRIX ============
def evaluate_approval_matrix(db: Session, order: Order, current_user: User) -> bool:
    """
    Evaluate approval matrix rules to determine if current_user can approve.
    Approval rules are managed by backend approval-rule configuration and are not hardcoded here.
    Returns True if user is authorized, raises HTTPException if not.
    """
    rules = db.query(ApprovalRule).filter(
        ApprovalRule.is_active == True
    ).order_by(ApprovalRule.priority).all()
    
    # Calculate order quantity
    order_quantity = sum(Decimal(str(item.quantity_ordered)) for item in order.items)
    
    # Evaluate each rule in priority order
    for rule in rules:
        matches = False
        
        if rule.rule_type == "quantity":
            min_qty = rule.condition_json.get("min_quantity", 0)
            if order_quantity >= Decimal(str(min_qty)):
                matches = True
        elif rule.rule_type == "department":
            dept = rule.condition_json.get("department")
            if current_user.department == dept:
                matches = True
        elif rule.rule_type == "user":
            user_id = rule.condition_json.get("user_id")
            if current_user.id == user_id:
                matches = True
        elif rule.rule_type == "value":
            # Placeholder for value-based approval (requires pricing)
            value = rule.condition_json.get("min_value", 0)
            # In Phase 2, we don't have pricing, so skip
            continue
        
        if matches:
            # Check if current user has the required role/user match
            if rule.approver_role_id:
                if current_user.role_id != rule.approver_role_id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Order requires approval from role {rule.approver_role_id}"
                    )
                return True
            elif rule.approver_user_id:
                if current_user.id != rule.approver_user_id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Order requires approval from specific user"
                    )
                return True
    
    # No rule matched — if an approver was designated, only they may approve
    if order.approver_id:
        if current_user.id == order.approver_id:
            return True
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the designated approver can approve this order"
        )
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not authorized to approve this order — no matching approval rule and no approver designated"
    )


# ============ RESERVATION LOGIC (delegates to service with row locking) ============
def reserve_stock(db: Session, order: Order, user: User) -> List[str]:
    """
    Reserve inventory for all order items. All-or-nothing with row locking.
    Returns list of errors if any item cannot be reserved.
    Raises HTTPException if any check fails.
    """
    errors = svc_reserve(db, order.items, user.id)
    if errors:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": "Insufficient stock to approve order", "errors": errors}
        )
    return []


def release_reservation(db: Session, order: Order):
    """Release all reservations for an order. Uses row locking."""
    svc_release(db, order.items)


def dispatch_stock(db: Session, order: Order, dispatch_items: List, user: User, partial: bool = False) -> List:
    """
    Consume reserved stock and create ledger entries. Uses row locking.
    Returns list of errors (empty if all succeeded).
    """
    dispatch_map = {item.item_id: Decimal(str(item.quantity)) for item in dispatch_items}
    return svc_dispatch(
        db,
        order_items=order.items,
        dispatch_map=dispatch_map,
        order_id=order.id,
        order_number=order.order_number,
        user_id=user.id,
        partial=partial,
    )


# ============ ORDER CRUD ============

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
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            order_number = generate_order_number(db, "ORD-{YYYY}-{SEQ}", current_user.location or "HO")

            # Create order
            order = Order(
                order_number=order_number,
                vendor_id=order_data.vendor_id,
                status=OrderStatus.DRAFT,
                remarks=order_data.remarks,
                delivery_address=order_data.delivery_address,
                created_by=current_user.id
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
    sort_by: str = Query("recent_activity", regex="^(recent_activity|created_date)$"),
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
    
    total = query.count()
    skip = (page - 1) * size
    orders = query.options(
        selectinload(Order.items).selectinload(OrderItem.item),
        selectinload(Order.timeline_entries),
        selectinload(Order.vendor),
    ).offset(skip).limit(size).all()
    total_pages = (total + size - 1) // size
    return {
        "items": [OrderResponse.model_validate(o) for o in orders],
        "total": total,
        "page": page,
        "size": size,
        "pages": total_pages
    }


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


# ============ STATE TRANSITIONS ============

@router.post("/{order_id}/submit-requisition", response_model=OrderResponse)
def submit_requisition(
    order_id: int,
    approver_id: int = Query(..., description="User ID of the approver"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Draft -> Pending Requisition with PDF generation and approver assignment."""
    order = db.query(Order).options(
        selectinload(Order.items).selectinload(OrderItem.item),
        joinedload(Order.vendor),
    ).filter(
        Order.id == order_id,
        Order.deleted_at == None
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if order.status != OrderStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition from {order.status} to pending_requisition"
        )
    
    if not order.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order must have at least one item"
        )
    
    # Validate approver
    approver = db.query(User).filter(
        User.id == approver_id,
        User.is_active == True,
        User.deleted_at == None
    ).first()
    if not approver:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Approver not found or inactive"
        )
    
    # Generate requisition PDF
    try:
        # Get settings for branding
        company_settings = db.query(Settings).first()
        settings_dict = {
            "company_name": company_settings.company_name if company_settings else "Cloud9",
            "company_address": company_settings.company_address if company_settings else "",
            "header_text": company_settings.pdf_header_text if company_settings else "",
            "footer_text": company_settings.pdf_footer_text if company_settings else ""
        }
        
        # Prepare items for PDF
        pdf_items = []
        for order_item in order.items:
            pdf_items.append({
                "sku": order_item.item.sku,
                "name": order_item.item.name,
                "quantity": str(order_item.quantity_ordered),
                "description": order_item.item.description or ""
            })
        
        # Generate PDF
        pdf_generator = PDFGenerator(
            company_name=settings_dict.get("company_name", "Cloud9")
        )
        
        order_url = f"http://localhost:8000/orders/{order.id}"
        pdf_content = pdf_generator.generate_requisition(
            order_number=order.order_number,
            vendor_name=order.vendor.name,
            vendor_address=order.vendor.address or "",
            items=pdf_items,
            remarks=order.remarks or "",
            delivery_address=order.delivery_address or "",
            requested_by=current_user.full_name or current_user.email,
            company_address=settings_dict.get("company_address", ""),
            order_url=order_url,
            header_text=settings_dict.get("header_text", ""),
            footer_text=settings_dict.get("footer_text", "")
        )
        
        # Save PDF to storage
        storage = get_storage_backend()
        storage_path = storage.save(
            f"orders/{order.id}/requisition.pdf",
            pdf_content
        )
        
        # Create document record
        document = Document(
            order_id=order.id,
            file_name=f"requisition_{order.order_number}.pdf",
            file_type="pdf",
            storage_path=storage_path,
            doc_category="requisition",
            version=1,
            version_status="current",
            notes="Auto-generated requisition PDF",
            uploaded_by=current_user.id
        )
        db.add(document)
        db.flush()
        
    except Exception as e:
        logger.error("PDF generation failed for order %s: %s", order.id, str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate requisition PDF: {str(e)}"
        )
    
    order.status = OrderStatus.PENDING_REQUISITION
    order.approver_id = approver.id
    add_timeline_entry(db, order, "requisition_generated", current_user)
    db.flush()
    
    # Create notification for approver
    from app.models import Notification
    notification = Notification(
        user_id=approver.id,
        actor_id=current_user.id,
        title="Requisition Pending Approval",
        message=f"Requisition {order.order_number} requires your approval.",
        type="approval_required",
        related_entity_type="order",
        related_entity_id=order.id,
        is_read=False
    )
    db.add(notification)
    
    log_audit(db, user_id=current_user.id, action="order.submitted", entity_type="order", entity_id=order.id)
    db.commit()
    db.refresh(order)
    
    # Send requisition created email (non-blocking)
    try:
        send_requisition_created_email(db, order)
    except Exception as e:
        logger.warning("Email send failed for order %s: %s", order.id, str(e))
    
    return order


@router.post("/{order_id}/upload-signed", response_model=OrderResponse)
def upload_signed_requisition(
    order_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Pending Requisition -> Signed Requisition Uploaded with file upload."""
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.deleted_at == None
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if order.status != OrderStatus.PENDING_REQUISITION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition from {order.status} to signed_requisition_uploaded"
        )
    
    # Handle file upload
    try:
        content = file.file.read()
        
        # Validate file type
        if not file.filename or not file.filename.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be PDF or image (JPG, PNG)"
            )
        
        if len(content) > 1 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File too large (max 1MB)"
            )

        # For image uploads, validate 1:1 aspect ratio
        if file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            try:
                from io import BytesIO
                from PIL import Image as PILImage
                img = PILImage.open(BytesIO(content))
                w, h = img.size
                allowed_diff = int(max(w, h) * 0.02)
                if abs(w - h) > allowed_diff:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Signature image must be square (1:1 aspect ratio). Got {w}x{h}"
                    )
            except HTTPException:
                raise
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Could not validate image dimensions. Ensure the file is a valid image."
                )
        
        # Get previous requisition document (to mark as superseded)
        previous_doc = db.query(Document).filter(
            Document.order_id == order.id,
            Document.doc_category == "requisition",
            Document.version_status == "current"
        ).first()
        
        # Save signed file to storage (sanitized filename)
        safe_filename = os.path.basename(file.filename) if file.filename else f"signed_{order.id}.pdf"
        storage = get_storage_backend()
        storage_path = storage.save(
            f"orders/{order.id}/signed_requisition_{safe_filename}",
            content
        )
        
        # Create new document with versioning
        new_version = (previous_doc.version + 1) if previous_doc else 1
        
        signed_doc = Document(
            order_id=order.id,
            file_name=file.filename,
            file_type=file.filename.rsplit(".", 1)[1].lower() if "." in file.filename else "pdf",
            storage_path=storage_path,
            doc_category="signed_requisition",
            version=new_version,
            version_status="current",
            parent_document_id=previous_doc.id if previous_doc else None,
            notes="Signed requisition uploaded by user",
            uploaded_by=current_user.id
        )
        db.add(signed_doc)
        
        # Mark previous document as superseded
        if previous_doc:
            previous_doc.version_status = "superseded"
        
        db.flush()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File upload failed: {str(e)}"
        )
    
    order.status = OrderStatus.SIGNED_REQUISITION_UPLOADED
    add_timeline_entry(db, order, "signed_uploaded", current_user)
    log_audit(db, user_id=current_user.id, action="order.signed_uploaded", entity_type="order", entity_id=order.id)
    db.commit()
    db.refresh(order)
    return order


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
    signature_data: str = Query(..., description="Base64-encoded signature image (with or without data:image/png;base64 prefix)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
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
        if not oi.item or oi.item.item_type != "returnable":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Item #{oi.item_id} is not returnable")
        if ret.quantity_returned <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Return quantity must be positive")

        remaining = oi.quantity_dispatched - oi.quantity_returned - oi.quantity_damaged
        if ret.quantity_returned + ret.quantity_damaged > remaining:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Item #{oi.item_id}: only {remaining} units left to return (dispatched: {oi.quantity_dispatched}, already returned: {oi.quantity_returned}, already damaged: {oi.quantity_damaged})"
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


@router.get("/{order_id}/download-pdf")
def download_order_pdf(
    order_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download order as a requisition PDF. Includes approver signature when available."""
    import os as _os
    from fastapi.responses import FileResponse as FastFileResponse
    import tempfile

    order = db.query(Order).options(
        selectinload(Order.items).selectinload(OrderItem.item),
        joinedload(Order.vendor),
    ).filter(
        Order.id == order_id,
        Order.deleted_at == None
    ).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    tmp_paths = []

    # Prefer to return the stored signed requisition PDF if it exists
    signed_doc = db.query(Document).filter(
        Document.order_id == order.id,
        Document.doc_category == "signed_requisition",
        Document.version_status == "current"
    ).order_by(Document.version.desc()).first()

    if signed_doc:
        try:
            storage = get_storage_backend()
            pdf_data = storage.read(signed_doc.storage_path)
            if pdf_data:
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
                tmp.write(pdf_data)
                tmp.close()
                tmp_paths.append(tmp.name)
                for p in tmp_paths:
                    background_tasks.add_task(_os.unlink, p)
                return FastFileResponse(
                    path=tmp.name,
                    media_type="application/pdf",
                    filename=f"{order.order_number}_requisition.pdf"
                )
        except Exception as e:
            logger.warning("Could not load existing PDF for order %s, regenerating: %s", order_id, str(e))

    items = [
        {
            "name": oi.item.name if oi.item else f"Item #{oi.item_id}",
            "sku": oi.item.sku if oi.item else "",
            "quantity": str(oi.quantity_ordered),
            "description": oi.item.description if oi.item else "",
        }
        for oi in order.items
    ]

    settings = db.query(Settings).first()

    creator = db.query(User).filter(User.id == order.created_by).first()

    # Look up approver signature from timeline + UserSignature
    approver_name = None
    approver_signature_base64 = None
    if order.status in ("approved", "dispatched", "delivered", "closed"):
        approval_entry = db.query(OrderTimeline).filter(
            OrderTimeline.order_id == order.id,
            OrderTimeline.action == "approved"
        ).order_by(OrderTimeline.id.desc()).first()
        if approval_entry:
            approver = db.query(User).options(
                selectinload(User.signature)
            ).filter(User.id == approval_entry.user_id).first()
            if approver:
                approver_name = approver.full_name or approver.email
                if approver.signature and approver.signature.signature_data:
                    approver_signature_base64 = approver.signature.signature_data

    pdf_gen = PDFGenerator(
        company_name=settings.company_name if settings else "Cloud9",
        logo_url=settings.company_logo_url if settings else None
    )

    pdf_bytes = pdf_gen.generate_requisition(
        order_number=order.order_number,
        vendor_name=order.vendor.name if order.vendor else "Unknown",
        vendor_address=order.vendor.address if order.vendor else "",
        items=items,
        remarks=order.remarks or "",
        delivery_address=order.delivery_address or "",
        requested_by=creator.full_name if creator else "Unknown",
        company_address=settings.company_address if settings else "",
        order_url=f"/orders/{order.id}",
        header_text=settings.pdf_header_text if settings else "",
        footer_text=settings.pdf_footer_text if settings else "",
        approver_name=approver_name,
        approver_signature_base64=approver_signature_base64,
    )

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp.write(pdf_bytes)
    tmp.close()
    tmp_paths.append(tmp.name)

    for p in tmp_paths:
        background_tasks.add_task(_os.unlink, p)

    return FastFileResponse(
        path=tmp.name,
        media_type="application/pdf",
        filename=f"{order.order_number}_requisition.pdf"
    )


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
