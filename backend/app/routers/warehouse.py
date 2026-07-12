from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_user, require_admin
from app.models import User, Warehouse, WarehouseZone, WarehouseRack, WarehouseShelf, WarehouseBin
from app.schemas import WarehouseResponse, WarehouseZoneResponse, WarehouseRackResponse, WarehouseShelfResponse, WarehouseBinResponse
from typing import List
from pydantic import BaseModel

router = APIRouter(prefix="/warehouses", tags=["Warehouse"])


# Request schemas
class WarehouseCreateRequest(BaseModel):
    name: str
    address: str = None


class ZoneCreateRequest(BaseModel):
    name: str


class RackCreateRequest(BaseModel):
    name: str


class ShelfCreateRequest(BaseModel):
    name: str


class BinCreateRequest(BaseModel):
    name: str


@router.get("", response_model=List[WarehouseResponse])
def list_warehouses(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all warehouses with their hierarchy."""
    skip = (page - 1) * size
    warehouses = db.query(Warehouse).filter(
        Warehouse.is_active == True
    ).offset(skip).limit(size).all()
    return warehouses


@router.post("", response_model=WarehouseResponse, status_code=status.HTTP_201_CREATED)
def create_warehouse(
    warehouse_data: WarehouseCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create a new warehouse."""
    warehouse = Warehouse(
        name=warehouse_data.name,
        address=warehouse_data.address
    )
    db.add(warehouse)
    db.commit()
    db.refresh(warehouse)
    return warehouse


@router.get("/{warehouse_id}", response_model=WarehouseResponse)
def get_warehouse(
    warehouse_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get warehouse with full hierarchy."""
    warehouse = db.query(Warehouse).filter(
        Warehouse.id == warehouse_id,
        Warehouse.is_active == True
    ).first()
    
    if not warehouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Warehouse not found"
        )
    return warehouse


# Zones
@router.post("/{warehouse_id}/zones", response_model=WarehouseZoneResponse, status_code=status.HTTP_201_CREATED)
def create_zone(
    warehouse_id: int,
    zone_data: ZoneCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create a zone in a warehouse."""
    warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    if not warehouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Warehouse not found"
        )
    
    zone = WarehouseZone(
        warehouse_id=warehouse_id,
        name=zone_data.name
    )
    db.add(zone)
    db.commit()
    db.refresh(zone)
    return zone


# Racks
@router.post("/{warehouse_id}/zones/{zone_id}/racks", response_model=WarehouseRackResponse, status_code=status.HTTP_201_CREATED)
def create_rack(
    warehouse_id: int,
    zone_id: int,
    rack_data: RackCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create a rack in a zone."""
    zone = db.query(WarehouseZone).filter(
        WarehouseZone.id == zone_id,
        WarehouseZone.warehouse_id == warehouse_id
    ).first()
    
    if not zone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zone not found"
        )
    
    rack = WarehouseRack(
        zone_id=zone_id,
        name=rack_data.name
    )
    db.add(rack)
    db.commit()
    db.refresh(rack)
    return rack


# Shelves
@router.post("/{warehouse_id}/zones/{zone_id}/racks/{rack_id}/shelves", response_model=WarehouseShelfResponse, status_code=status.HTTP_201_CREATED)
def create_shelf(
    warehouse_id: int,
    zone_id: int,
    rack_id: int,
    shelf_data: ShelfCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create a shelf in a rack."""
    rack = db.query(WarehouseRack).filter(
        WarehouseRack.id == rack_id,
        WarehouseRack.zone_id == zone_id
    ).first()
    
    if not rack:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rack not found"
        )
    
    shelf = WarehouseShelf(
        rack_id=rack_id,
        name=shelf_data.name
    )
    db.add(shelf)
    db.commit()
    db.refresh(shelf)
    return shelf


# Bins
@router.post("/{warehouse_id}/zones/{zone_id}/racks/{rack_id}/shelves/{shelf_id}/bins", response_model=WarehouseBinResponse, status_code=status.HTTP_201_CREATED)
def create_bin(
    warehouse_id: int,
    zone_id: int,
    rack_id: int,
    shelf_id: int,
    bin_data: BinCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create a bin in a shelf."""
    shelf = db.query(WarehouseShelf).filter(
        WarehouseShelf.id == shelf_id,
        WarehouseShelf.rack_id == rack_id
    ).first()
    
    if not shelf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shelf not found"
        )
    
    bin_obj = WarehouseBin(
        shelf_id=shelf_id,
        name=bin_data.name
    )
    db.add(bin_obj)
    db.commit()
    db.refresh(bin_obj)
    return bin_obj
