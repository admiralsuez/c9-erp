from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import InventoryItem, InventoryTransaction, OrderItem
from app.core.database import engine
import logging

logger = logging.getLogger(__name__)


def get_available_quantity(item: InventoryItem) -> Decimal:
    """Get the quantity available for ordering.
    
    For containers (is_container=True with children), returns sum of children's available.
    For parents with children, own stock is ignored — available comes from children.
    For standalone items, returns current_quantity - reserved_quantity.
    """
    if item.is_container or (item.children and len(item.children) > 0):
        return sum(
            (c.current_quantity - c.reserved_quantity)
            for c in item.children
            if not c.deleted_at
        )
    return item.current_quantity - item.reserved_quantity


def _lock_items(db: Session, item_ids: List[int]) -> dict:
    """Lock item rows in deterministic order (by ID) to prevent deadlocks.
    Returns dict of {id: InventoryItem} for locked rows.
    On SQLite, FOR UPDATE is silently ignored — safe for dev.
    On Postgres, this serializes concurrent access.
    """
    if not item_ids:
        return {}
    items = {}
    for item_id in sorted(item_ids):
        item = db.query(InventoryItem).filter(
            InventoryItem.id == item_id,
            InventoryItem.deleted_at == None
        ).with_for_update().first()
        if item:
            items[item.id] = item
    return items


def restock_item(
    db: Session,
    item_id: int,
    quantity: Decimal,
    reason: str,
    user_id: int,
) -> InventoryTransaction:
    """Add quantity to an item. Uses row locking."""
    locked = _lock_items(db, [item_id])
    item = locked.get(item_id)
    if not item:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    if quantity <= 0:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quantity must be positive")

    previous_quantity = item.current_quantity
    new_quantity = previous_quantity + quantity

    transaction = InventoryTransaction(
        item_id=item.id,
        transaction_type="stock_added",
        previous_quantity=previous_quantity,
        change_quantity=quantity,
        new_quantity=new_quantity,
        reference_type="restock",
        reason=reason,
        created_by=user_id,
    )
    db.add(transaction)
    item.current_quantity = new_quantity
    db.commit()
    db.refresh(transaction)
    return transaction


def adjust_item(
    db: Session,
    item_id: int,
    new_quantity: Decimal,
    reason: str,
    user_id: int,
) -> InventoryTransaction:
    """Set item quantity to an exact value. Uses row locking."""
    locked = _lock_items(db, [item_id])
    item = locked.get(item_id)
    if not item:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    if new_quantity < 0:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quantity cannot be negative")

    previous_quantity = item.current_quantity
    change_quantity = new_quantity - previous_quantity

    transaction = InventoryTransaction(
        item_id=item.id,
        transaction_type="adjustment",
        previous_quantity=previous_quantity,
        change_quantity=change_quantity,
        new_quantity=new_quantity,
        reason=reason,
        created_by=user_id,
    )
    db.add(transaction)
    item.current_quantity = new_quantity
    db.commit()
    db.refresh(transaction)
    return transaction


def reserve_stock(db: Session, order_items: List[OrderItem], user_id: int) -> List[str]:
    """Reserve inventory for order items. All-or-nothing with row locking.
    Returns list of errors if any item cannot be reserved.
    """
    item_ids = list(set(oi.item_id for oi in order_items))
    locked = _lock_items(db, item_ids)

    errors = []
    for oi in order_items:
        item = locked.get(oi.item_id)
        if not item:
            errors.append(f"Item #{oi.item_id}: not found")
            continue
        available = get_available_quantity(item)
        if available < oi.quantity_ordered:
            errors.append(
                f"Item {item.sku} ({item.name}): need {oi.quantity_ordered}, "
                f"available {available}"
            )
            continue

    if errors:
        return errors

    for oi in order_items:
        item = locked.get(oi.item_id)
        oi.quantity_reserved = oi.quantity_ordered
        item.reserved_quantity += oi.quantity_ordered

    return []


def release_reservation(db: Session, order_items: List[OrderItem]):
    """Release all reservations for order items. Uses row locking."""
    item_ids = list(set(oi.item_id for oi in order_items if oi.quantity_reserved > 0))
    locked = _lock_items(db, item_ids)

    for oi in order_items:
        item = locked.get(oi.item_id)
        if not item:
            continue
        item.reserved_quantity -= oi.quantity_reserved
        oi.quantity_reserved = Decimal("0")


def dispatch_stock(
    db: Session,
    order_items: List[OrderItem],
    dispatch_map: dict,
    order_id: int,
    order_number: str,
    user_id: int,
    partial: bool = False,
):
    """Consume reserved stock and create ledger entries. Uses row locking.
    dispatch_map: {item_id: Decimal(quantity)}
    """
    item_ids = list(set(oi.item_id for oi in order_items if oi.item_id in dispatch_map))
    locked = _lock_items(db, item_ids)
    errors = []

    for oi in order_items:
        if oi.item_id not in dispatch_map:
            if not partial:
                errors.append(f"Item #{oi.item_id} not included in dispatch")
            continue

        dispatch_qty = dispatch_map[oi.item_id]
        item = locked.get(oi.item_id)
        if not item:
            errors.append(f"Item #{oi.item_id}: not found")
            continue

        if dispatch_qty > oi.quantity_reserved:
            errors.append(
                f"Item {item.sku}: cannot dispatch {dispatch_qty}, "
                f"only {oi.quantity_reserved} reserved"
            )
            continue

        previous_qty = item.current_quantity
        new_qty = previous_qty - dispatch_qty

        transaction = InventoryTransaction(
            item_id=item.id,
            transaction_type="dispatch",
            previous_quantity=previous_qty,
            change_quantity=-dispatch_qty,
            new_quantity=new_qty,
            reference_type="order",
            reference_id=order_id,
            reason=f"Dispatch for order {order_number}",
            created_by=user_id,
        )
        db.add(transaction)
        item.current_quantity = new_qty
        item.reserved_quantity -= dispatch_qty
        oi.quantity_dispatched += dispatch_qty

    if errors and not partial:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": "Cannot dispatch order", "errors": errors},
        )

    return errors
