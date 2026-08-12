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
