import logging
from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, require_permission
from app.core.database import get_db
from app.models import InventoryItem, InventoryTransaction, User
from app.schemas import (
    AdjustmentRequest,
    InventoryItemResponse,
    InventoryTransactionResponse,
    RestockRequest,
)
from app.services.inventory_service import adjust_item as svc_adjust, restock_item as svc_restock

router = APIRouter(prefix="/inventory", tags=["Inventory"])
logger = logging.getLogger(__name__)

@router.post("/items/{item_id}/adjust-quantity", response_model=InventoryItemResponse)
def adjust_item_quantity(
    item_id: int,
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("inventory.edit"))
):
    """Adjust item quantity and create transaction record."""
    item = db.query(InventoryItem).filter(
        InventoryItem.id == item_id,
        InventoryItem.deleted_at == None
    ).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    
    quantity_change = body.get("quantity_change", 0)
    reason = body.get("reason", "Manual adjustment")
    
    if not quantity_change:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="quantity_change is required"
        )
    
    try:
        quantity_change = float(quantity_change)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="quantity_change must be a number"
        )
    
    previous_qty = item.current_quantity
    new_qty = previous_qty + Decimal(str(quantity_change))
    
    # Prevent negative quantities for consumables
    if new_qty < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot reduce quantity below zero"
        )
    
    # Create transaction
    transaction = InventoryTransaction(
        item_id=item.id,
        transaction_type="adjustment",
        previous_quantity=previous_qty,
        change_quantity=Decimal(str(quantity_change)),
        new_quantity=new_qty,
        reason=reason,
        created_by=current_user.id
    )
    db.add(transaction)
    
    # Update item quantity
    item.current_quantity = new_qty
    
    db.commit()
    db.refresh(item)
    
    logger.info(
        "ADJUSTED item(%d) '%s' qty from %s to %s by %s (reason: %s)",
        item.id, item.sku, previous_qty, new_qty, current_user.email, reason
    )
    
    return item
@router.patch("/items/{item_id}/stock-status", response_model=InventoryItemResponse)
def update_stock_status(
    item_id: int,
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("inventory.edit"))
):
    """Update item stock status (active | expired | damaged)."""
    item = db.query(InventoryItem).filter(
        InventoryItem.id == item_id,
        InventoryItem.deleted_at == None
    ).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    
    stock_status = body.get("stock_status", "").lower()
    valid_statuses = ["active", "expired", "damaged"]
    
    if stock_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"stock_status must be one of: {', '.join(valid_statuses)}"
        )
    
    previous_status = item.stock_status
    item.stock_status = stock_status
    
    db.commit()
    db.refresh(item)
    
    logger.info(
        "UPDATED item(%d) '%s' stock_status from %s to %s by %s",
        item.id, item.sku, previous_status, stock_status, current_user.email
    )
    
    return item
@router.get("/items/{item_id}/transactions", response_model=List[InventoryTransactionResponse])
def get_item_transactions(
    item_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get transaction history for an item."""
    item = db.query(InventoryItem).filter(
        InventoryItem.id == item_id,
        InventoryItem.deleted_at == None
    ).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    
    skip = (page - 1) * size
    transactions = db.query(InventoryTransaction).filter(
        InventoryTransaction.item_id == item_id
    ).order_by(InventoryTransaction.created_at.desc()).offset(skip).limit(size).all()
    
    return transactions
@router.post("/restock", response_model=InventoryTransactionResponse)
def restock_item(
    restock_data: RestockRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("inventory.dispatch"))
):
    """Restock an item (add to current_quantity via ledger, row-locked)."""
    item = db.query(InventoryItem).filter(InventoryItem.id == restock_data.item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.parent_id is None:
        has_children = db.query(InventoryItem).filter(InventoryItem.parent_id == item.id, InventoryItem.deleted_at == None).first() is not None
        if has_children:
            raise HTTPException(status_code=400, detail="Cannot restock a parent item. Stock is managed on individual variants.")
    transaction = svc_restock(
        db,
        item_id=restock_data.item_id,
        quantity=Decimal(str(restock_data.quantity)),
        reason=restock_data.reason,
        user_id=current_user.id,
    )
    return transaction
@router.post("/adjust", response_model=InventoryTransactionResponse)
def adjust_item(
    adjust_data: AdjustmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("inventory.edit"))
):
    """Adjust item quantity to a specific value via ledger (row-locked)."""
    item = db.query(InventoryItem).filter(InventoryItem.id == adjust_data.item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.parent_id is None:
        has_children = db.query(InventoryItem).filter(InventoryItem.parent_id == item.id, InventoryItem.deleted_at == None).first() is not None
        if has_children:
            raise HTTPException(status_code=400, detail="Cannot adjust a parent item. Stock is managed on individual variants.")
    transaction = svc_adjust(
        db,
        item_id=adjust_data.item_id,
        new_quantity=Decimal(str(adjust_data.new_quantity)),
        reason=adjust_data.reason,
        user_id=current_user.id,
    )
    return transaction
