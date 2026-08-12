"""Database models.

Split from the former app/models.py monolith into domain-focused modules.
All models are re-exported here so existing `from app.models import X`
imports keep working.
"""

from app.models.settings import Settings
from app.models.user import (
    Role,
    Permission,
    RolePermission,
    User,
    RefreshToken,
    PasswordResetToken,
    UserSignature,
)
from app.models.vendor import VendorType, Vendor
from app.models.warehouse import (
    Warehouse,
    WarehouseZone,
    WarehouseRack,
    WarehouseShelf,
    WarehouseBin,
)
from app.models.inventory import (
    InventoryCategory,
    InventoryItem,
    InventoryItemAttribute,
    InventoryTransaction,
    InventoryItemImage,
    SerialNumber,
)
from app.models.audit import AuditLog
from app.models.order import (
    ApprovalRule,
    Order,
    Notification,
    OrderItem,
    ReturnPhoto,
    OrderTimeline,
    Document,
)
from app.models.communication import EmailTemplate, EmailLog
from app.models.reporting import Report, ScheduledReport, DashboardMetric

__all__ = [
    "Settings",
    "Role",
    "Permission",
    "RolePermission",
    "User",
    "RefreshToken",
    "PasswordResetToken",
    "UserSignature",
    "VendorType",
    "Vendor",
    "Warehouse",
    "WarehouseZone",
    "WarehouseRack",
    "WarehouseShelf",
    "WarehouseBin",
    "InventoryCategory",
    "InventoryItem",
    "InventoryItemAttribute",
    "InventoryTransaction",
    "InventoryItemImage",
    "SerialNumber",
    "AuditLog",
    "ApprovalRule",
    "Order",
    "Notification",
    "OrderItem",
    "ReturnPhoto",
    "OrderTimeline",
    "Document",
    "EmailTemplate",
    "EmailLog",
    "Report",
    "ScheduledReport",
    "DashboardMetric",
]
