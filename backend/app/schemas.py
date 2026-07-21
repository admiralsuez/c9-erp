from __future__ import annotations
from pydantic import BaseModel, EmailStr, ConfigDict, computed_field, field_validator
from datetime import datetime
from typing import Optional, List


# ============ AUTH ============
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserBase(BaseModel):
    full_name: str
    email: EmailStr
    department: Optional[str] = None
    location: str = "HO"

class PermissionSchema(BaseModel):
    id: int
    code: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RoleSchema(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    permissions: List[PermissionSchema] = []

    model_config = ConfigDict(from_attributes=True)


class UserResponse(UserBase):
    id: int
    email: str
    role: Optional[RoleSchema] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: Optional['UserResponse'] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# ============ USERS & ROLES ============



class RoleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    permission_ids: List[int] = []


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permission_ids: Optional[List[int]] = None




class UserCreate(UserBase):
    password: str
    role_id: int


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    department: Optional[str] = None
    role_id: Optional[int] = None
    location: Optional[str] = None



# ============ AUTH ============
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: Optional[UserResponse] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# ============ SETTINGS ============
class SettingsResponse(BaseModel):
    id: int
    company_name: Optional[str] = None
    company_logo_url: Optional[str] = None
    company_gst: Optional[str] = None
    company_address: Optional[str] = None
    company_contact: Optional[str] = None
    order_number_format: str
    requisition_number_format: str
    pdf_header_text: Optional[str] = None
    pdf_footer_text: Optional[str] = None
    default_low_stock_threshold: float
    ho_prefix: str = "HO"
    llf_prefix: str = "LLF"
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SettingsUpdate(BaseModel):
    company_name: Optional[str] = None
    company_logo_url: Optional[str] = None
    company_gst: Optional[str] = None
    company_address: Optional[str] = None
    company_contact: Optional[str] = None
    order_number_format: Optional[str] = None
    requisition_number_format: Optional[str] = None
    pdf_header_text: Optional[str] = None
    pdf_footer_text: Optional[str] = None
    default_low_stock_threshold: Optional[float] = None
    ho_prefix: Optional[str] = None
    llf_prefix: Optional[str] = None


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
    is_active: bool
    created_at: datetime
    updated_at: datetime

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


# ============ INVENTORY CATEGORIES ============
class InventoryCategoryBase(BaseModel):
    name: str
    parent_id: Optional[int] = None


class InventoryCategoryCreate(InventoryCategoryBase):
    pass


class InventoryCategoryResponse(InventoryCategoryBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


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


# ============ INVENTORY ITEMS ============
class InventoryItemBase(BaseModel):
    name: str
    sku: str
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
    created_at: datetime
    updated_at: datetime
    children: List['InventoryItemResponse'] = []
    attributes: Optional[dict] = None

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

class InventoryItemImageResponse(BaseModel):
    id: int
    item_id: int
    image_type: str
    image_url: str
    uploaded_by: Optional[int] = None
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)

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



class InventoryItemDetailResponse(InventoryItemResponse):
    transactions: List[InventoryTransactionResponse] = []
    images: List['InventoryItemImageResponse'] = []
    serial_numbers: List['SerialNumberResponse'] = []
    parent: Optional['InventoryItemResponse'] = None


# ============ INVENTORY ITEM IMAGES ============

class InventoryItemImageCreate(BaseModel):
    image_type: str


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

# ============ RESTOCK & ADJUST ============
class RestockRequest(BaseModel):
    item_id: int
    quantity: float
    reason: str


class AdjustmentRequest(BaseModel):
    item_id: int
    new_quantity: float
    reason: str


# ============ PAGINATION ============
class PaginationParams(BaseModel):
    page: int = 1
    size: int = 20

    def get_offset(self) -> int:
        return (self.page - 1) * self.size


class PaginatedResponse(BaseModel):
    items: List
    total: int
    page: int
    size: int
    total_pages: int


# ============ AUDIT LOG ============
class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    ip_address: Optional[str] = None
    previous_value: Optional[dict] = None
    new_value: Optional[dict] = None
    reason: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


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
    created_at: datetime
    item: Optional['InventoryItemResponse'] = None
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
    vendor: Optional['VendorResponse'] = None

    model_config = ConfigDict(from_attributes=True)


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


class DispatchItemRequest(BaseModel):
    item_id: int
    quantity: float


class DispatchRequestBody(BaseModel):
    items: List[DispatchItemRequest]
    partial: bool = False  # Allow partial dispatch


class ApprovalRuleCondition(BaseModel):
    pass  # Dynamic JSON


class ApprovalRuleCreateRequest(BaseModel):
    name: str
    rule_type: str  # quantity | value | department | user
    condition_json: dict
    approver_role_id: Optional[int] = None
    approver_user_id: Optional[int] = None
    priority: int = 0


class ApprovalRuleResponse(BaseModel):
    id: int
    name: str
    rule_type: str
    condition_json: dict
    approver_role_id: Optional[int] = None
    approver_user_id: Optional[int] = None
    priority: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============ PHASE 3: DOCUMENTS ============
class DocumentUploadRequest(BaseModel):
    doc_category: str  # requisition | signed_requisition | other
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


# ============ USER SIGNATURE ============
class SignatureResponse(BaseModel):
    id: int
    user_id: int
    signature_data: str
    uploaded_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SignatureUpdate(BaseModel):
    signature_data: str
