from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from datetime import datetime


# ============ VENDORS ============
class VendorBase(BaseModel):
    name: str
    vendor_type: Optional[str] = None
    vendor_type_id: Optional[int] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    gst: Optional[str] = None
    notes: Optional[str] = None


class VendorCreate(VendorBase):
    pass


class VendorUpdate(BaseModel):
    name: Optional[str] = None
    vendor_type: Optional[str] = None
    vendor_type_id: Optional[int] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    gst: Optional[str] = None
    notes: Optional[str] = None


class VendorResponse(VendorBase):
    id: int
    parent_id: Optional[int] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    children: List[VendorResponse] = []

    model_config = ConfigDict(from_attributes=True)


class VendorSummaryResponse(VendorResponse):
    total_orders: int = 0
    total_quantity_ordered: float = 0


class VendorTypeResponse(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class VendorTypeCreate(BaseModel):
    name: str
