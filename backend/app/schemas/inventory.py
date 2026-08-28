from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, computed_field, field_validator
from datetime import datetime


# ============ INVENTORY CATEGORIES ============
class InventoryCategoryBase(BaseModel):
    name: str
    parent_id: Optional[int] = None


class InventoryCategoryCreate(InventoryCategoryBase):
    pass


class InventoryCategoryResponse(InventoryCategoryBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# ============ INVENTORY ITEMS ============
class InventoryItemBase(BaseModel):
    name: str
    sku: str
    erp_number: Optional[str] = None
    barcode: Optional[str] = None
    category_id: Optional[int] = None
    item_type: str = "consumable"
    minimum_quantity: float = 0
    bin_id: Optional[int] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    parent_id: Optional[int] = None
    is_container: bool = False
    attributes: Optional[dict] = None


class InventoryItemCreate(InventoryItemBase):
    current_quantity: float = 0
    is_draft: bool = False  # Save as draft instead of publishing immediately


class InventoryItemChildCreate(BaseModel):
    name: str
    sku: str
    barcode: Optional[str] = None
    item_type: str = "consumable"
    current_quantity: float = 0
    minimum_quantity: float = 0
    description: Optional[str] = None
    primary_attribute: Optional[str] = None
    secondary_attribute: Optional[str] = None
    notes: Optional[str] = None


class InventoryItemBatchCreate(BaseModel):
    parent: InventoryItemCreate
    children: List[InventoryItemChildCreate] = []


class InventoryItemUpdate(BaseModel):
    name: Optional[str] = None
    category_id: Optional[int] = None
    item_type: Optional[str] = None
    minimum_quantity: Optional[float] = None
    bin_id: Optional[int] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    parent_id: Optional[int] = None
    is_container: Optional[bool] = None
    attributes: Optional[dict] = None
    expiry_date: Optional[datetime] = None
    allow_no_expiry: Optional[bool] = None
    stock_status: Optional[str] = None  # active | expired | damaged
    current_quantity: Optional[float] = None  # Allow direct quantity edits


class InventoryTransactionResponse(BaseModel):
    id: int
    transaction_type: str
    previous_quantity: float
    change_quantity: float
    new_quantity: float
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    reason: Optional[str] = None
    created_by: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InventoryItemResponse(InventoryItemBase):
    id: int
    current_quantity: float
    reserved_quantity: float
    is_active: bool
    is_container: bool = False
    is_draft: bool = False
    expiry_date: Optional[datetime] = None
    allow_no_expiry: bool = True
    stock_status: str = "active"  # active | expired | damaged
    created_at: datetime
    updated_at: datetime
    children: List['InventoryItemResponse'] = []
    attributes: Optional[dict] = None
    front_image_url: Optional[str] = None
    back_image_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    @field_validator('attributes', mode='before')
    @classmethod
    def convert_attributes(cls, v):
        """Convert ORM attributes list to dict."""
        if isinstance(v, list) and v:
            # Convert list of ORM objects to dict
            return {attr.attribute_name: attr.attribute_value for attr in v}
        return v or None

    @computed_field
    @property
    def available_quantity(self) -> float:
        if self.is_container and self.children:
            return sum(c.available_quantity for c in self.children)
        return self.current_quantity - self.reserved_quantity


class InventoryItemDetailResponse(InventoryItemResponse):
    transactions: List[InventoryTransactionResponse] = []
    images: List['InventoryItemImageResponse'] = []
    serial_numbers: List['SerialNumberResponse'] = []
    parent: Optional['InventoryItemResponse'] = None


# ============ INVENTORY ITEM IMAGES ============
class InventoryItemImageCreate(BaseModel):
    image_type: str


class InventoryItemImageResponse(BaseModel):
    id: int
    item_id: int
    image_type: str
    image_url: str
    uploaded_by: Optional[int] = None
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============ SERIAL NUMBERS ============
class SerialNumberCreate(BaseModel):
    count: int = 1
    base_serial: Optional[str] = None
    batch_id: Optional[str] = None
    condition: str = "new"


class SerialNumberBatchCreate(BaseModel):
    start_serial: str
    end_serial: str
    batch_id: Optional[str] = None
    condition: str = "new"


class SerialNumberImportCreate(BaseModel):
    serials: List[str]
    batch_id: Optional[str] = None
    condition: str = "new"


class SerialNumberUpdate(BaseModel):
    unit_condition: Optional[str] = None
    location_bin_id: Optional[int] = None
    assigned_to_order_id: Optional[int] = None
    notes: Optional[str] = None


class SerialNumberResponse(BaseModel):
    id: int
    item_id: int
    serial_number: str
    batch_id: Optional[str] = None
    unit_condition: str = "new"
    location_bin_id: Optional[int] = None
    assigned_to_order_id: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============ RESTOCK & ADJUST ============
class RestockRequest(BaseModel):
    item_id: int
    quantity: float
    reason: str


class AdjustmentRequest(BaseModel):
    item_id: int
    new_quantity: float
    reason: str


# Rebuild models that use forward references to ensure they can find the classes defined below them
# This is necessary for Pydantic v2 + FastAPI route registration
InventoryItemDetailResponse.model_rebuild()
InventoryItemResponse.model_rebuild()
