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
