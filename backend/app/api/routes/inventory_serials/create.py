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

@router.post("/{item_id}/serials/import", response_model=List[SerialNumberResponse], status_code=status.HTTP_201_CREATED)
def import_serials(
    item_id: int,
    request: SerialNumberImportCreate,
    db: Session = Depends(get_db)
):
    """
    Import a list of existing serial numbers (for units that already have manufacturer serials).

    Args:
        item_id: The inventory item ID
        request: SerialNumberImportCreate with serials list, batch_id, condition

    Returns:
        List of created SerialNumberResponse objects
    """
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Inventory item {item_id} not found")

    if not request.serials:
        raise HTTPException(status_code=400, detail="Serial list cannot be empty")

    if len(request.serials) > 10000:
        raise HTTPException(status_code=400, detail="Maximum 10000 serials per import")

    try:
        serials = serial_number_service.bulk_import_serials(
            db=db,
            item_id=item_id,
            serials=request.serials,
            batch_id=request.batch_id,
            unit_condition=request.condition
        )
        return serials
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import serials: {str(e)}")
