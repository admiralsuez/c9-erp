"""
API endpoints for inventory serial number management
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.schemas import (
    SerialNumberResponse,
    SerialNumberCreate,
    SerialNumberBatchCreate,
    SerialNumberUpdate
)
from app.models import SerialNumber, InventoryItem
from app.services.serial_number_service import serial_number_service

router = APIRouter(
    prefix="/inventory",
    tags=["inventory-serials"]
)


@router.post("/{item_id}/serials/single", response_model=List[SerialNumberResponse], status_code=status.HTTP_201_CREATED)
def create_single_serials(
    item_id: int,
    request: SerialNumberCreate,
    db: Session = Depends(get_db)
):
    """
    Create one or more individual serial numbers for an item
    
    Args:
        item_id: The inventory item ID
        request: SerialNumberCreate with count, batch_id, condition, and optional base_serial
        
    Returns:
        List of created SerialNumberResponse objects
    """
    
    # Verify item exists
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inventory item {item_id} not found"
        )
    
    # Validate count
    if request.count < 1 or request.count > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Count must be between 1 and 1000"
        )
    
    try:
        serials = serial_number_service.generate_single_serials(
            db=db,
            item_id=item_id,
            count=request.count,
            batch_id=request.batch_id,
            unit_condition=request.condition or "new",
            base_serial=request.base_serial
        )
        return serials
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create serials: {str(e)}"
        )


@router.post("/{item_id}/serials/range", response_model=List[SerialNumberResponse], status_code=status.HTTP_201_CREATED)
def create_range_serials(
    item_id: int,
    request: SerialNumberBatchCreate,
    db: Session = Depends(get_db)
):
    """
    Create serial numbers from a range (e.g., SN1000-SN1099)
    
    Args:
        item_id: The inventory item ID
        request: SerialNumberBatchCreate with start_serial, end_serial, batch_id, condition
        
    Returns:
        List of created SerialNumberResponse objects
    """
    
    # Verify item exists
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inventory item {item_id} not found"
        )
    
    try:
        serials = serial_number_service.generate_range_serials(
            db=db,
            item_id=item_id,
            start_serial=request.start_serial,
            end_serial=request.end_serial,
            batch_id=request.batch_id,
            unit_condition=request.condition or "new"
        )
        return serials
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create serials: {str(e)}"
        )


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


@router.get("/{item_id}/serials/search/{serial_number}", response_model=SerialNumberResponse)
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


@router.patch("/{item_id}/serials/{serial_id}", response_model=SerialNumberResponse)
def update_serial(
    item_id: int,
    serial_id: int,
    request: SerialNumberUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a serial number's condition or assignment
    
    Args:
        item_id: The inventory item ID
        serial_id: The serial number ID
        request: SerialNumberUpdate with optional condition and order_id
        
    Returns:
        Updated SerialNumberResponse
    """
    
    # Verify item exists
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inventory item {item_id} not found"
        )
    
    # Get serial
    serial = db.query(SerialNumber).filter(
        SerialNumber.id == serial_id,
        SerialNumber.item_id == item_id
    ).first()
    
    if not serial:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Serial number {serial_id} not found for item {item_id}"
        )
    
    try:
        # Update condition if provided
        if request.condition:
            serial = serial_number_service.update_condition(
                db=db,
                serial_id=serial_id,
                new_condition=request.condition
            )
        
        # Update order assignment if provided
        if request.assigned_to_order_id is not None:
            if request.assigned_to_order_id == 0:
                # 0 means unassign
                serial = serial_number_service.unassign_from_order(
                    db=db,
                    serial_id=serial_id
                )
            else:
                serial = serial_number_service.assign_to_order(
                    db=db,
                    serial_id=serial_id,
                    order_id=request.assigned_to_order_id
                )
        
        return serial
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update serial: {str(e)}"
        )


@router.post("/{item_id}/serials/{serial_id}/assign/{order_id}", response_model=SerialNumberResponse)
def assign_serial_to_order(
    item_id: int,
    serial_id: int,
    order_id: int,
    db: Session = Depends(get_db)
):
    """
    Assign a serial number to an order (for dispatch)
    
    Args:
        item_id: The inventory item ID
        serial_id: The serial number ID
        order_id: The order ID to assign to
        
    Returns:
        Updated SerialNumberResponse
    """
    
    # Verify item exists
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inventory item {item_id} not found"
        )
    
    # Get serial
    serial = db.query(SerialNumber).filter(
        SerialNumber.id == serial_id,
        SerialNumber.item_id == item_id
    ).first()
    
    if not serial:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Serial number {serial_id} not found for item {item_id}"
        )
    
    try:
        serial = serial_number_service.assign_to_order(
            db=db,
            serial_id=serial_id,
            order_id=order_id
        )
        return serial
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assign serial: {str(e)}"
        )


@router.post("/{item_id}/serials/{serial_id}/unassign", response_model=SerialNumberResponse)
def unassign_serial_from_order(
    item_id: int,
    serial_id: int,
    db: Session = Depends(get_db)
):
    """
    Remove a serial number from its assigned order
    
    Args:
        item_id: The inventory item ID
        serial_id: The serial number ID
        
    Returns:
        Updated SerialNumberResponse
    """
    
    # Verify item exists
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inventory item {item_id} not found"
        )
    
    # Get serial
    serial = db.query(SerialNumber).filter(
        SerialNumber.id == serial_id,
        SerialNumber.item_id == item_id
    ).first()
    
    if not serial:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Serial number {serial_id} not found for item {item_id}"
        )
    
    try:
        serial = serial_number_service.unassign_from_order(
            db=db,
            serial_id=serial_id
        )
        return serial
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unassign serial: {str(e)}"
        )


@router.delete("/{item_id}/serials/{serial_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_serial(
    item_id: int,
    serial_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a serial number
    
    Args:
        item_id: The inventory item ID
        serial_id: The serial number ID to delete
    """
    
    # Verify item exists
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inventory item {item_id} not found"
        )
    
    # Get serial
    serial = db.query(SerialNumber).filter(
        SerialNumber.id == serial_id,
        SerialNumber.item_id == item_id
    ).first()
    
    if not serial:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Serial number {serial_id} not found for item {item_id}"
        )
    
    try:
        serial_number_service.delete_serial(
            db=db,
            serial_id=serial_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete serial: {str(e)}"
        )


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
