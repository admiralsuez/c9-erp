from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from datetime import datetime

from app.schemas.inventory import InventoryItemResponse
from app.schemas.vendor import VendorResponse


# ============ PHASE 2: ORDERS ============
class OrderItemCreateRequest(BaseModel):
    item_id: int
    quantity_ordered: float
    serial_ids: Optional[List[int]] = None


class OrderItemResponse(BaseModel):
    id: int
    item_id: int
    quantity_ordered: float
    quantity_reserved: float
    quantity_dispatched: float
    quantity_returned: float = 0
    quantity_damaged: float = 0
    return_reason: Optional[str] = None  # damaged | not_needed
    return_status: Optional[str] = None  # pending | completed
    created_at: datetime
    item: Optional[InventoryItemResponse] = None
    serial_ids: Optional[List[int]] = []

    model_config = ConfigDict(from_attributes=True)


class ReturnItemRequest(BaseModel):
    order_item_id: int
    item_id: int
    quantity_returned: float
    quantity_damaged: float = 0
    reason: Optional[str] = None


class ReturnOrderRequest(BaseModel):
    items: List[ReturnItemRequest]


class OrderCreateRequest(BaseModel):
    vendor_id: int
    items: List[OrderItemCreateRequest]
    remarks: Optional[str] = None
    delivery_address: Optional[str] = None
    order_date: Optional[datetime] = None  # Optional backdate for order


class OrderUpdateRequest(BaseModel):
    vendor_id: Optional[int] = None
    items: Optional[List[OrderItemCreateRequest]] = None
    remarks: Optional[str] = None
    delivery_address: Optional[str] = None


class OrderTimelineEntryResponse(BaseModel):
    id: int
    action: str
    comments: Optional[str] = None
    user_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    id: int
    order_number: str
    vendor_id: int
    status: str
    remarks: Optional[str] = None
    delivery_address: Optional[str] = None
    created_by: Optional[int] = None
    approver_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse] = []
    timeline_entries: List[OrderTimelineEntryResponse] = []
    vendor: Optional[VendorResponse] = None

    model_config = ConfigDict(from_attributes=True)


# ============ NOTIFICATIONS ============
class NotificationResponse(BaseModel):
    id: int
    user_id: int
    actor_id: Optional[int] = None
    actor_name: Optional[str] = None
    title: str
    message: Optional[str] = None
    type: str
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[int] = None
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============ DISPATCH ============
class DispatchItemRequest(BaseModel):
    item_id: int
    quantity: float


class DispatchRequestBody(BaseModel):
    items: List[DispatchItemRequest]
    partial: bool = False  # Allow partial dispatch


# ============ PHASE 3: DOCUMENTS ============
class DocumentUploadRequest(BaseModel):
    doc_category: str  # requisition | signed_requisition | other
    challan_book_number: Optional[str] = None  # challan book number for delivery challan
    notes: Optional[str] = None


class DocumentResponse(BaseModel):
    id: int
    order_id: Optional[int] = None
    file_name: str
    file_type: str
    doc_category: Optional[str] = None
    version: int
    parent_document_id: Optional[int] = None
    version_status: str  # current | superseded
    challan_book_number: Optional[str] = None  # challan book number for delivery challan
    notes: Optional[str] = None
    uploaded_by: Optional[int] = None
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentVersionHistoryResponse(BaseModel):
    id: int
    version: int
    version_status: str
    uploaded_at: datetime
    uploaded_by: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
