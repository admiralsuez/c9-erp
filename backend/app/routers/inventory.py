from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.core.database import get_db
from app.core.auth import get_current_user, require_permission
from app.models import (
    User, InventoryItem, InventoryCategory, InventoryTransaction,
    WarehouseBin
)
from sqlalchemy.orm import selectinload
from app.services.audit_service import log_audit
from app.services.inventory_service import restock_item as svc_restock, adjust_item as svc_adjust
from app.schemas import (
    InventoryCategoryCreate, InventoryCategoryResponse,
    InventoryItemCreate, InventoryItemUpdate, InventoryItemResponse,
    InventoryItemDetailResponse, InventoryItemBatchCreate,
    RestockRequest, AdjustmentRequest,
    InventoryTransactionResponse
)
from typing import List
from decimal import Decimal
from datetime import datetime, timezone
import logging

router = APIRouter(prefix="/inventory", tags=["Inventory"])
logger = logging.getLogger(__name__)


# ============ INVENTORY CATEGORIES ============

@router.get("/categories", response_model=List[InventoryCategoryResponse])
def list_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all inventory categories."""
    categories = db.query(InventoryCategory).all()
    return categories


@router.post("/categories", response_model=InventoryCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category_data: InventoryCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("inventory.create"))
):
    """Create an inventory category."""
    # Check if category with this name already exists
    existing = db.query(InventoryCategory).filter(
        InventoryCategory.name == category_data.name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Category with this name already exists"
        )
    
    category = InventoryCategory(
        name=category_data.name,
        parent_id=category_data.parent_id
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.put("/categories/{category_id}", response_model=InventoryCategoryResponse)
def update_category(
    category_id: int,
    category_data: InventoryCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("inventory.create"))
):
    """Update an inventory category."""
    category = db.query(InventoryCategory).filter(InventoryCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    existing = db.query(InventoryCategory).filter(
        InventoryCategory.name == category_data.name,
        InventoryCategory.id != category_id
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Category with this name already exists")
    category.name = category_data.name
    category.parent_id = category_data.parent_id
    db.commit()
    db.refresh(category)
    return category


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("inventory.create"))
):
    """Delete an inventory category."""
    category = db.query(InventoryCategory).filter(InventoryCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    items_count = db.query(InventoryItem).filter(InventoryItem.category_id == category_id).count()
    if items_count > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot delete category: {items_count} item(s) still reference it"
        )
    db.delete(category)
    db.commit()


# ============ INVENTORY ITEMS ============

@router.get("/items")
def list_items(
    search: str = Query(None),
    category_id: int = Query(None),
    low_stock: bool = Query(False),
    item_type: str = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List inventory items with filtering and search. Returns paginated response."""
    query = db.query(InventoryItem).filter(InventoryItem.deleted_at == None)
    
    # Search by name, SKU, or barcode
    if search:
        query = query.filter(
            or_(
                InventoryItem.name.ilike(f"%{search}%"),
                InventoryItem.sku.ilike(f"%{search}%"),
                InventoryItem.barcode.ilike(f"%{search}%")
            )
        )
    
    # Filter by category
    if category_id:
        query = query.filter(InventoryItem.category_id == category_id)
    
    # Filter by item type
    if item_type:
        query = query.filter(InventoryItem.item_type == item_type)
    
    # Filter low stock items (uses global threshold when item minimum is 0, excludes parents)
    if low_stock:
        parent_ids = set(row[0] for row in db.query(InventoryItem.parent_id).filter(
            InventoryItem.parent_id != None,
            InventoryItem.deleted_at == None
        ).distinct().all() if row[0] is not None)
        if parent_ids:
            query = query.filter(~InventoryItem.id.in_(parent_ids))

        from app.models import Settings as SettingsModel
        settings_row = db.query(SettingsModel).first()
        default_threshold = float(settings_row.default_low_stock_threshold) if settings_row and settings_row.default_low_stock_threshold else 10
        query = query.filter(
            or_(
                and_(InventoryItem.minimum_quantity > 0, InventoryItem.current_quantity <= InventoryItem.minimum_quantity),
                and_(or_(InventoryItem.minimum_quantity == 0, InventoryItem.minimum_quantity == None), InventoryItem.current_quantity <= default_threshold),
            )
        )
    
    # Get total count before pagination
    total = query.count()
    
    skip = (page - 1) * size
    items = query.options(
        selectinload(InventoryItem.children)
    ).offset(skip).limit(size).all()
    
    total_pages = (total + size - 1) // size
    
    return {
        "items": [InventoryItemResponse.model_validate(i) for i in items],
        "total": total,
        "page": page,
        "size": size,
        "pages": total_pages
    }


@router.post("/items", response_model=InventoryItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(
    item_data: InventoryItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("inventory.create"))
):
    """Create an inventory item with opening balance transaction."""
    # Check if SKU already exists
    existing_sku = db.query(InventoryItem).filter(
        InventoryItem.sku == item_data.sku
    ).first()
    
    if existing_sku:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Item with this SKU already exists"
        )
    
    # Check if barcode already exists (if provided)
    if item_data.barcode:
        existing_barcode = db.query(InventoryItem).filter(
            InventoryItem.barcode == item_data.barcode
        ).first()
        
        if existing_barcode:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Item with this barcode already exists"
            )
    
    # Verify category exists (if provided)
    if item_data.category_id:
        category = db.query(InventoryCategory).filter(
            InventoryCategory.id == item_data.category_id
        ).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
    
    # Verify bin exists (if provided)
    if item_data.bin_id:
        bin_obj = db.query(WarehouseBin).filter(
            WarehouseBin.id == item_data.bin_id
        ).first()
        if not bin_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bin not found"
            )
    
    # Validate one-level parent: parent must exist and must not itself be a variant
    if item_data.parent_id:
        parent_item = db.query(InventoryItem).filter(
            InventoryItem.id == item_data.parent_id,
            InventoryItem.deleted_at == None
        ).first()
        if not parent_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent item not found"
            )
        if parent_item.parent_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selected parent is itself a variant — cannot nest further (one level only)"
            )
    
    item = InventoryItem(
        name=item_data.name,
        sku=item_data.sku,
        barcode=item_data.barcode,
        qr_code_data=item_data.barcode,  # Use barcode as QR data for now
        category_id=item_data.category_id,
        parent_id=item_data.parent_id,
        item_type=item_data.item_type,
        current_quantity=Decimal(str(item_data.current_quantity)),
        reserved_quantity=Decimal("0"),
        minimum_quantity=Decimal(str(item_data.minimum_quantity)),
        bin_id=item_data.bin_id,
        description=item_data.description,
        image_url=item_data.image_url
    )
    db.add(item)
    db.flush()  # Get the item ID before creating transaction
    
    # Create opening balance transaction
    if item_data.current_quantity > 0:
        transaction = InventoryTransaction(
            item_id=item.id,
            transaction_type="opening_balance",
            previous_quantity=Decimal("0"),
            change_quantity=Decimal(str(item_data.current_quantity)),
            new_quantity=Decimal(str(item_data.current_quantity)),
            reference_type=None,
            reference_id=None,
            reason="Opening balance",
            created_by=current_user.id
        )
        db.add(transaction)
    
    db.commit()
    db.refresh(item)
    logger.info(
        "CREATED item(%d) '%s' type=%s qty=%s by %s",
        item.id, item.sku, item.item_type, item_data.current_quantity, current_user.email
    )
    return item


@router.post("/items/batch", response_model=InventoryItemResponse, status_code=status.HTTP_201_CREATED)
def create_items_batch(
    data: InventoryItemBatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("inventory.create"))
):
    """Create a parent item with its children in one request."""
    parent_data = data.parent
    # Check SKU uniqueness
    existing = db.query(InventoryItem).filter(InventoryItem.sku == parent_data.sku).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"SKU '{parent_data.sku}' already exists")
    if parent_data.barcode:
        existing_bc = db.query(InventoryItem).filter(InventoryItem.barcode == parent_data.barcode).first()
        if existing_bc:
            raise HTTPException(status_code=409, detail=f"Barcode '{parent_data.barcode}' already exists")
    if parent_data.category_id:
        cat = db.query(InventoryCategory).filter(InventoryCategory.id == parent_data.category_id).first()
        if not cat:
            raise HTTPException(status_code=404, detail="Category not found")

    parent = InventoryItem(
        name=parent_data.name, sku=parent_data.sku,
        barcode=parent_data.barcode, qr_code_data=parent_data.barcode,
        category_id=parent_data.category_id, item_type=parent_data.item_type,
        current_quantity=Decimal(str(parent_data.current_quantity)),
        reserved_quantity=Decimal("0"),
        minimum_quantity=Decimal(str(parent_data.minimum_quantity)),
        bin_id=parent_data.bin_id, description=parent_data.description,
        image_url=parent_data.image_url
    )
    db.add(parent)
    db.flush()

    if parent_data.current_quantity > 0:
        txn = InventoryTransaction(
            item_id=parent.id, transaction_type="opening_balance",
            previous_quantity=Decimal("0"),
            change_quantity=Decimal(str(parent_data.current_quantity)),
            new_quantity=Decimal(str(parent_data.current_quantity)),
            reason="Opening balance", created_by=current_user.id
        )
        db.add(txn)

    # Create children
    for child_data in data.children:
        if child_data.barcode:
            existing_bc = db.query(InventoryItem).filter(InventoryItem.barcode == child_data.barcode).first()
            if existing_bc:
                raise HTTPException(status_code=409, detail=f"Child barcode '{child_data.barcode}' already exists")
        desc_parts = []
        if child_data.primary_attribute:
            desc_parts.append(f"Primary: {child_data.primary_attribute}")
        if child_data.secondary_attribute:
            desc_parts.append(f"Secondary: {child_data.secondary_attribute}")
        if child_data.notes:
            desc_parts.append(f"Notes: {child_data.notes}")
        child_desc = " | ".join(desc_parts) if desc_parts else child_data.description
        child = InventoryItem(
            name=child_data.name, sku=child_data.sku,
            barcode=child_data.barcode, qr_code_data=child_data.barcode,
            parent_id=parent.id, item_type=child_data.item_type,
            current_quantity=Decimal(str(child_data.current_quantity)),
            reserved_quantity=Decimal("0"),
            minimum_quantity=Decimal(str(child_data.minimum_quantity)),
            description=child_desc or child_data.description
        )
        db.add(child)
        db.flush()
        if child_data.current_quantity > 0:
            txn = InventoryTransaction(
                item_id=child.id, transaction_type="opening_balance",
                previous_quantity=Decimal("0"),
                change_quantity=Decimal(str(child_data.current_quantity)),
                new_quantity=Decimal(str(child_data.current_quantity)),
                reason="Opening balance", created_by=current_user.id
            )
            db.add(txn)

    db.commit()
    db.refresh(parent)
    logger.info(
        "CREATED parent(%d) '%s' + %d children by %s",
        parent.id, parent.sku, len(data.children), current_user.email
    )
    return parent


@router.get("/items/{item_id}", response_model=InventoryItemDetailResponse)
def get_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get item details including transaction history."""
    item = db.query(InventoryItem).options(
        selectinload(InventoryItem.children),
        selectinload(InventoryItem.parent),
    ).filter(
        InventoryItem.id == item_id,
        InventoryItem.deleted_at == None
    ).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    
    return item


@router.patch("/items/{item_id}", response_model=InventoryItemResponse)
def update_item(
    item_id: int,
    item_data: InventoryItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("inventory.edit"))
):
    """Update item metadata (NOT quantities)."""
    item = db.query(InventoryItem).filter(
        InventoryItem.id == item_id,
        InventoryItem.deleted_at == None
    ).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    
    update_data = item_data.model_dump(exclude_unset=True)
    
    # Validate one-level parent on update
    if 'parent_id' in update_data and update_data['parent_id'] is not None:
        # The item itself must not already have children
        has_children = db.query(InventoryItem).filter(
            InventoryItem.parent_id == item_id,
            InventoryItem.deleted_at == None
        ).count()
        if has_children > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Item has existing variants — cannot assign a parent to a parent item"
            )
        # The target parent must exist and must not itself be a variant
        parent_item = db.query(InventoryItem).filter(
            InventoryItem.id == update_data['parent_id'],
            InventoryItem.deleted_at == None
        ).first()
        if not parent_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent item not found"
            )
        if parent_item.id == item_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An item cannot be its own parent"
            )
        if parent_item.parent_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Target parent is itself a variant — cannot nest further (one level only)"
            )
    
    for field, value in update_data.items():
        setattr(item, field, value)
    
    db.commit()
    db.refresh(item)
    return item


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("inventory.edit"))
):
    """Soft delete an item."""
    item = db.query(InventoryItem).filter(
        InventoryItem.id == item_id,
        InventoryItem.deleted_at == None
    ).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    
    item.deleted_at = datetime.now(timezone.utc)
    db.commit()


@router.post("/items/{item_id}/restore", response_model=InventoryItemResponse)
def restore_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("inventory.edit"))
):
    """Restore a soft-deleted item."""
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    
    if not item.deleted_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Item is not deleted"
        )
    
    item.deleted_at = None
    db.commit()
    db.refresh(item)
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


@router.get("/items/barcode/{barcode}", response_model=InventoryItemResponse)
def get_item_by_barcode(
    barcode: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lookup item by barcode."""
    item = db.query(InventoryItem).filter(
        InventoryItem.barcode == barcode,
        InventoryItem.deleted_at == None
    ).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    
    return item


# ============ RESTOCK & ADJUST ============

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
