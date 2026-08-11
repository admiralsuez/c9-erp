from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


# ============ WAREHOUSE HIERARCHY ============
class WarehouseBinResponse(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class WarehouseShelfResponse(BaseModel):
    id: int
    name: str
    bins: List[WarehouseBinResponse] = []

    model_config = ConfigDict(from_attributes=True)


class WarehouseRackResponse(BaseModel):
    id: int
    name: str
    shelves: List[WarehouseShelfResponse] = []

    model_config = ConfigDict(from_attributes=True)


class WarehouseZoneResponse(BaseModel):
    id: int
    name: str
    racks: List[WarehouseRackResponse] = []

    model_config = ConfigDict(from_attributes=True)


class WarehouseResponse(BaseModel):
    id: int
    name: str
    address: Optional[str] = None
    is_active: bool
    zones: List[WarehouseZoneResponse] = []

    model_config = ConfigDict(from_attributes=True)
