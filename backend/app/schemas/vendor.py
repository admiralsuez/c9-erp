from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, model_validator
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
    parent_id: Optional[int] = None


class VendorUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[int] = None
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
    deleted_at: Optional[datetime] = None
    children: List[VendorResponse] = []

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def filter_deleted_children(self) -> "VendorResponse":
        if self.children:
            self.children = [c for c in self.children if c.deleted_at is None]
        return self


class VendorSummaryResponse(VendorResponse):
    total_orders: int = 0
    total_quantity_ordered: float = 0


class VendorTypeResponse(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class VendorTypeCreate(BaseModel):
    name: str
