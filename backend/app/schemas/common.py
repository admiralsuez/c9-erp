from __future__ import annotations
from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, ConfigDict
from datetime import datetime

T = TypeVar("T")


# ============ SETTINGS ============
class SettingsResponse(BaseModel):
    id: int
    company_name: Optional[str] = None
    company_logo_url: Optional[str] = None
    company_gst: Optional[str] = None
    company_address: Optional[str] = None
    company_contact: Optional[str] = None
    order_number_format: str = "ORD-{YYYY}-{SEQ}"
    requisition_number_format: str = "REQ-{YYYY}-{SEQ}"
    pdf_header_text: Optional[str] = None
    pdf_footer_text: Optional[str] = None
    default_low_stock_threshold: float = 10.0
    ho_prefix: str = "HO"
    llf_prefix: str = "LLF"
    updated_at: Optional[datetime] = None

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


# ============ PAGINATION ============
class PaginationParams(BaseModel):
    page: int = 1
    size: int = 20

    def get_offset(self) -> int:
        return (self.page - 1) * self.size


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard envelope for paginated list responses.

    Every list endpoint across the API returns this shape so the frontend can
    rely on a single parsing path. ``items`` carries the per-row payload;
    ``total`` is the unpaginated row count; ``pages`` is the total page count
    (computed as ``(total + size - 1) // size``, never negative).
    """
    items: List[T]
    total: int
    page: int
    size: int
    pages: int

    @classmethod
    def build(cls, items: List[T], total: int, page: int, size: int) -> "PaginatedResponse[T]":
        """Construct from raw items, computing pages automatically."""
        pages = (total + size - 1) // size if size > 0 else 0
        return cls(items=items, total=total, page=page, size=size, pages=pages)


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


# ============ APPROVAL RULES ============
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


# ============ ERRORS ============
class ErrorResponse(BaseModel):
    status: str = "error"
    message: str
    error_code: str
    details: Optional[dict] = None
    timestamp: str
    path: str
    detail: str = ""  # Legacy alias of message
