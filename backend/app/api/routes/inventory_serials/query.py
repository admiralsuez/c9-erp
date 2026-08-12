"""Serial number management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.schemas import (
    SerialNumberResponse,
    SerialNumberCreate,
    SerialNumberBatchCreate,
    SerialNumberImportCreate,
    SerialNumberUpdate
)
from app.models import SerialNumber, InventoryItem
from app.services.serial_number_service import serial_number_service

router = APIRouter(prefix="/inventory", tags=["inventory-serials"])

@router.get("/{item_id}/serials", response_model=List[SerialNumberResponse])
def get_item_serials(
    item_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    condition: Optional[str] = Query(None),
    batch_id: Optional[str] = Query(None),
    unassigned_only: bool = Query(False),
    db: Session = Depends(get_db)
):
    """
    Get serial numbers for an item with optional filtering
    
    Args:
        item_id: The inventory item ID
        skip: Number of records to skip
        limit: Maximum number of records to return
        condition: Filter by condition (new, used, damaged, refurbished)
        batch_id: Filter by batch ID
        unassigned_only: Only return serials not assigned to orders
        
    Returns:
        List of SerialNumberResponse objects
    """
    
    # Verify item exists
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inventory item {item_id} not found"
        )
    
    # Build query
    query = db.query(SerialNumber).filter(SerialNumber.item_id == item_id)
    
    # Apply filters
    if condition:
        valid_conditions = {"new", "used", "damaged", "refurbished"}
        if condition not in valid_conditions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid condition: {condition}"
            )
        query = query.filter(SerialNumber.unit_condition == condition)
    
    if batch_id:
        query = query.filter(SerialNumber.batch_id == batch_id)
    
    if unassigned_only:
        query = query.filter(SerialNumber.assigned_to_order_id == None)
    
    # Sort and paginate
    serials = query.order_by(SerialNumber.created_at.desc()).offset(skip).limit(limit).all()
    return serials

@router.get("/{item_id}/serials/search-serial/{serial_number}", response_model=SerialNumberResponse)
def search_serial_by_number(
    item_id: int,
    serial_number: str,
    db: Session = Depends(get_db)
):
    """
    Search for a specific serial number within an item
    
    Args:
        item_id: The inventory item ID
        serial_number: The serial number to search for
        
    Returns:
        SerialNumberResponse for the serial, or 404 if not found
    """
    
    # Verify item exists
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inventory item {item_id} not found"
        )
    
    serial = serial_number_service.get_serial_by_number(
        db=db,
        item_id=item_id,
        serial_number=serial_number
    )
    
    if not serial:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Serial number '{serial_number}' not found for item {item_id}"
        )
    
    return serial

@router.get("/search/global/{serial_number}", response_model=SerialNumberResponse)
def search_serial_globally(
    serial_number: str,
    db: Session = Depends(get_db)
):
    """
    Search for a serial number across all items (global search)
    
    Args:
        serial_number: The serial number to search for
        
    Returns:
        SerialNumberResponse for the serial, or 404 if not found
    """
    
    serial = db.query(SerialNumber).filter(
        SerialNumber.serial_number == serial_number
    ).first()
    
    if not serial:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Serial number '{serial_number}' not found"
        )
    
    return serial

@router.get("/{item_id}/serials/batch/{batch_id}", response_model=List[SerialNumberResponse])
def get_batch_serials(
    item_id: int,
    batch_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all serial numbers in a batch
    
    Args:
        item_id: The inventory item ID
        batch_id: The batch ID
        
    Returns:
        List of SerialNumberResponse objects
    """
    
    # Verify item exists
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inventory item {item_id} not found"
        )
    
    serials = serial_number_service.get_serials_by_batch(
        db=db,
        batch_id=batch_id
    )
    
    # Filter to only this item
    serials = [s for s in serials if s.item_id == item_id]
    
    return serials

@router.get("/order/{order_id}/serials", response_model=List[SerialNumberResponse])
def get_order_serials(
    order_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all serial numbers assigned to an order
    
    Args:
        order_id: The order ID
        
    Returns:
        List of SerialNumberResponse objects
    """
    
    serials = serial_number_service.get_serials_by_order(
        db=db,
        order_id=order_id
    )
    
    return serials
