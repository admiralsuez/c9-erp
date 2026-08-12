from decimal import Decimal
from datetime import datetime, timezone
from enum import Enum
from typing import List

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import ApprovalRule, Order, OrderTimeline, Settings, User
from app.services.inventory_service import (
    reserve_stock as svc_reserve,
    release_reservation as svc_release,
    dispatch_stock as svc_dispatch,
)


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


def generate_order_number(db: Session, settings_format: str, location: str = "HO", attempt: int = 0, custom_date: datetime = None) -> str:
    """Generate unique order number using location-based prefix (HO/LLF).
    
    Args:
        db: Database session
        settings_format: Format string
        location: Location (HO/LLF)
        attempt: Retry attempt number
        custom_date: Optional custom date for order number generation (for backdate)
    """
    if custom_date:
        year = custom_date.year
    else:
        year = datetime.now(timezone.utc).year
    
    settings = db.query(Settings).first()
    prefix = (settings.llf_prefix if location == "LLF" else settings.ho_prefix) if settings else ("LLF" if location == "LLF" else "HO")
    
    # Count orders for the given year
    if custom_date:
        count = db.query(func.count(Order.id)).filter(
            func.extract('year', Order.created_at) == year
        ).scalar() or 0
    else:
        count = db.query(func.count(Order.id)).filter(
            func.extract('year', Order.created_at) == year
        ).scalar() or 0
    
    seq = count + 1 + attempt  # attempt offset prevents duplicate sequence on retry
    
    # Apply settings format template (e.g. "ORD-{YYYY}-{SEQ}"), prefixing with location
    if not settings_format:
        settings_format = "ORD-{YYYY}-{SEQ}"
    formatted = (
        settings_format.replace("{YYYY}", str(year))
        .replace("{YEAR}", str(year))
        .replace("{SEQ}", f"{seq:03d}")
    )
    return f"{prefix}-{formatted}"


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
