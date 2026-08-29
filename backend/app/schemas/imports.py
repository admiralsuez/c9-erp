"""
Import schemas for bulk CSV imports of vendors, items, and orders.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime


# ============ IMPORT REQUEST/RESPONSE MODELS ============

class VendorImportRow(BaseModel):
    """Single vendor row from CSV"""
    name: str
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

    @field_validator('name')
    @classmethod
    def name_required(cls, v):
        if not v or not v.strip():
            raise ValueError('Vendor name is required')
        return v.strip()


class ItemImportRow(BaseModel):
    """Single item row from CSV"""
    name: str
    sku: str
    category_id: Optional[int] = None
    item_type: str = 'consumable'
    current_quantity: float = 0
    minimum_quantity: float = 0
    erp_number: Optional[str] = None
    barcode: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None

    @field_validator('name')
    @classmethod
    def name_required(cls, v):
        if not v or not v.strip():
            raise ValueError('Item name is required')
        return v.strip()

    @field_validator('sku')
    @classmethod
    def sku_required(cls, v):
        if not v or not v.strip():
            raise ValueError('SKU is required')
        return v.strip()

    @field_validator('item_type')
    @classmethod
    def item_type_valid(cls, v):
        if v not in ['consumable', 'returnable']:
            raise ValueError('Item type must be "consumable" or "returnable"')
        return v


class OrderImportRow(BaseModel):
    """Single order row from CSV"""
    vendor_id: int
    item_id: int
    quantity_ordered: float
    order_date: Optional[str] = None
    remarks: Optional[str] = None
    delivery_address: Optional[str] = None
    challan_book_number: Optional[str] = None

    @field_validator('vendor_id')
    @classmethod
    def vendor_id_required(cls, v):
        if v is None or v <= 0:
            raise ValueError('Vendor ID is required and must be positive')
        return v

    @field_validator('item_id')
    @classmethod
    def item_id_required(cls, v):
        if v is None or v <= 0:
            raise ValueError('Item ID is required and must be positive')
        return v

    @field_validator('quantity_ordered')
    @classmethod
    def quantity_valid(cls, v):
        if v is None or v <= 0:
            raise ValueError('Quantity ordered must be greater than 0')
        return v


# ============ IMPORT RESULT MODELS ============

class ImportError(BaseModel):
    """Single row error"""
    row_number: int
    reason: str
    values: Optional[dict] = None


class ImportResult(BaseModel):
    """Result of an import operation"""
    success: bool
    total_rows: int
    successful: int
    failed: int
    errors: List[ImportError] = []
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "total_rows": 100,
                "successful": 98,
                "failed": 2,
                "errors": [
                    {
                        "row_number": 5,
                        "reason": "Duplicate SKU: SKU-001",
                        "values": {"name": "Item", "sku": "SKU-001"}
                    }
                ],
                "message": "Imported 98 vendors successfully. 2 rows had errors."
            }
        }


# ============ TEMPLATES ============

class CSVTemplate(BaseModel):
    """CSV template with headers and sample data"""
    filename: str
    headers: List[str]
    sample_rows: List[List[str]]


def get_vendor_template() -> CSVTemplate:
    """Get vendor import CSV template"""
    return CSVTemplate(
        filename="vendors_template.csv",
        headers=["name", "vendor_type_id", "contact_person", "phone", "email", "address", "city", "state", "pincode", "gst", "notes"],
        sample_rows=[
            ["ABC Traders", "1", "John Smith", "+91-9876543210", "john@abc.com", "123 Business St", "Mumbai", "MH", "400001", "27AABCU1234H1Z0", "Reliable vendor"],
            ["XYZ Supplies", "2", "Jane Doe", "+91-8765432109", "jane@xyz.com", "456 Commerce Ave", "Delhi", "DL", "110001", "07AABCT5678H9Z0", ""],
        ]
    )


def get_item_template() -> CSVTemplate:
    """Get item import CSV template"""
    return CSVTemplate(
        filename="items_template.csv",
        headers=["name", "sku", "category_id", "item_type", "current_quantity", "minimum_quantity", "erp_number", "barcode", "description", "parent_id"],
        sample_rows=[
            ["Office Chair", "OFC-001", "1", "consumable", "50", "10", "ERP-001", "BC001", "Ergonomic office chair", ""],
            ["Desk Lamp", "LAMP-001", "1", "returnable", "25", "5", "ERP-002", "BC002", "LED desk lamp", "1"],
        ]
    )


def get_order_template() -> CSVTemplate:
    """Get order import CSV template"""
    return CSVTemplate(
        filename="orders_template.csv",
        headers=["vendor_id", "item_id", "quantity_ordered", "order_date", "remarks", "delivery_address", "challan_book_number"],
        sample_rows=[
            ["1", "1", "10", "2026-08-28", "Urgent delivery", "Office Building A", "CB-001"],
            ["2", "2", "5", "2026-08-29", "", "Warehouse B", "CB-002"],
        ]
    )
