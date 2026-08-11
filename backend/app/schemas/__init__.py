"""Schemas package.

Split from the original monolithic ``app/schemas.py`` into focused domain
modules. All schemas are re-exported here so that existing imports of the form
``from app.schemas import X`` continue to work unchanged.
"""
from __future__ import annotations

from app.schemas.auth import (
    LoginRequest,
    UserBase,
    PermissionSchema,
    RoleSchema,
    UserResponse,
    TokenResponse,
    RefreshTokenRequest,
    RoleCreate,
    RoleUpdate,
    UserCreate,
    UserUpdate,
    PasswordResetRequest,
    PasswordResetConfirm,
    PasswordResetResponse,
    SignatureResponse,
    SignatureUpdate,
)
from app.schemas.vendor import (
    VendorBase,
    VendorCreate,
    VendorUpdate,
    VendorResponse,
    VendorSummaryResponse,
    VendorTypeResponse,
    VendorTypeCreate,
)
from app.schemas.inventory import (
    InventoryCategoryBase,
    InventoryCategoryCreate,
    InventoryCategoryResponse,
    InventoryItemBase,
    InventoryItemCreate,
    InventoryItemChildCreate,
    InventoryItemBatchCreate,
    InventoryItemUpdate,
    InventoryTransactionResponse,
    InventoryItemResponse,
    InventoryItemImageResponse,
    SerialNumberResponse,
    InventoryItemDetailResponse,
    InventoryItemImageCreate,
    SerialNumberCreate,
    SerialNumberBatchCreate,
    SerialNumberImportCreate,
    SerialNumberUpdate,
    RestockRequest,
    AdjustmentRequest,
)
from app.schemas.warehouse import (
    WarehouseBinResponse,
    WarehouseShelfResponse,
    WarehouseRackResponse,
    WarehouseZoneResponse,
    WarehouseResponse,
)
from app.schemas.order import (
    OrderItemCreateRequest,
    OrderItemResponse,
    ReturnItemRequest,
    ReturnOrderRequest,
    OrderCreateRequest,
    OrderUpdateRequest,
    OrderTimelineEntryResponse,
    OrderResponse,
    NotificationResponse,
    DispatchItemRequest,
    DispatchRequestBody,
    DocumentUploadRequest,
    DocumentResponse,
    DocumentVersionHistoryResponse,
)
from app.schemas.common import (
    SettingsResponse,
    SettingsUpdate,
    PaginationParams,
    PaginatedResponse,
    AuditLogResponse,
    ApprovalRuleCondition,
    ApprovalRuleCreateRequest,
    ApprovalRuleResponse,
)

# Resolve forward references now that every schema is imported into a shared
# namespace. This mirrors the behavior of the original single-module file.
TokenResponse.model_rebuild()
OrderItemResponse.model_rebuild()
OrderResponse.model_rebuild()

__all__ = [
    # auth
    "LoginRequest",
    "UserBase",
    "PermissionSchema",
    "RoleSchema",
    "UserResponse",
    "TokenResponse",
    "RefreshTokenRequest",
    "RoleCreate",
    "RoleUpdate",
    "UserCreate",
    "UserUpdate",
    "PasswordResetRequest",
    "PasswordResetConfirm",
    "PasswordResetResponse",
    "SignatureResponse",
    "SignatureUpdate",
    # vendor
    "VendorBase",
    "VendorCreate",
    "VendorUpdate",
    "VendorResponse",
    "VendorSummaryResponse",
    "VendorTypeResponse",
    "VendorTypeCreate",
    # inventory
    "InventoryCategoryBase",
    "InventoryCategoryCreate",
    "InventoryCategoryResponse",
    "InventoryItemBase",
    "InventoryItemCreate",
    "InventoryItemChildCreate",
    "InventoryItemBatchCreate",
    "InventoryItemUpdate",
    "InventoryTransactionResponse",
    "InventoryItemResponse",
    "InventoryItemImageResponse",
    "SerialNumberResponse",
    "InventoryItemDetailResponse",
    "InventoryItemImageCreate",
    "SerialNumberCreate",
    "SerialNumberBatchCreate",
    "SerialNumberImportCreate",
    "SerialNumberUpdate",
    "RestockRequest",
    "AdjustmentRequest",
    # warehouse
    "WarehouseBinResponse",
    "WarehouseShelfResponse",
    "WarehouseRackResponse",
    "WarehouseZoneResponse",
    "WarehouseResponse",
    # order
    "OrderItemCreateRequest",
    "OrderItemResponse",
    "ReturnItemRequest",
    "ReturnOrderRequest",
    "OrderCreateRequest",
    "OrderUpdateRequest",
    "OrderTimelineEntryResponse",
    "OrderResponse",
    "NotificationResponse",
    "DispatchItemRequest",
    "DispatchRequestBody",
    "DocumentUploadRequest",
    "DocumentResponse",
    "DocumentVersionHistoryResponse",
    # common
    "SettingsResponse",
    "SettingsUpdate",
    "PaginationParams",
    "PaginatedResponse",
    "AuditLogResponse",
    "ApprovalRuleCondition",
    "ApprovalRuleCreateRequest",
    "ApprovalRuleResponse",
]
