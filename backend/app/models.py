from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Numeric, JSON, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from datetime import datetime


# ============ SETTINGS ============
class Settings(Base):
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True)
    company_name = Column(String(200))
    company_logo_url = Column(String(500))
    company_gst = Column(String(20))
    company_address = Column(Text)
    company_contact = Column(String(200))
    order_number_format = Column(String(50), default="ORD-{YYYY}-{SEQ}")
    requisition_number_format = Column(String(50), default="REQ-{YYYY}-{SEQ}")
    pdf_header_text = Column(Text)
    pdf_footer_text = Column(Text)
    default_low_stock_threshold = Column(Numeric(12, 2), default=10)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())


# ============ USERS & RBAC ============
class Role(Base):
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    
    permissions = relationship("Permission", secondary="role_permissions", back_populates="roles")


class Permission(Base):
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True)
    code = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    
    roles = relationship("Role", secondary="role_permissions", back_populates="permissions")


class RolePermission(Base):
    __tablename__ = "role_permissions"
    
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    permission_id = Column(Integer, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True)


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    full_name = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"))
    department = Column(String(100))
    is_active = Column(Boolean, default=True, nullable=False)
    deleted_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    
    role = relationship("Role")
    refresh_tokens = relationship("RefreshToken", back_populates="user")
    signature = relationship("UserSignature", uselist=False, back_populates="user")
    
    __table_args__ = (
        Index("idx_users_email", "email"),
        Index("idx_users_deleted_at", "deleted_at"),
        Index("idx_users_active_deleted", "is_active", "deleted_at"),
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(255), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    
    user = relationship("User", back_populates="refresh_tokens")


class UserSignature(Base):
    __tablename__ = "user_signatures"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    signature_data = Column(Text, nullable=False)  # base64 encoded PNG
    uploaded_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    
    user = relationship("User", back_populates="signature")


# ============ VENDORS ============
class Vendor(Base):
    __tablename__ = "vendors"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    name_normalized = Column(String(200), nullable=False, unique=True)
    vendor_type = Column(String(50))
    contact_person = Column(String(150))
    phone = Column(String(30))
    email = Column(String(150))
    email_contact = Column(String(150))  # Phase 4: distinct contact email for vendor portal
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(100))
    gst = Column(String(20))
    notes = Column(Text)
    vendor_token = Column(String(32), unique=True)  # Phase 4: DEPRECATED - kept for migration compat
    vendor_token_hash = Column(String(64), unique=True)  # Phase 8: SHA-256 hash of vendor token
    vendor_token_expires_at = Column(DateTime(timezone=True))  # Phase 4: token expiry
    allow_portal = Column(Boolean, default=True, nullable=False)  # Phase 4: portal access flag
    is_active = Column(Boolean, default=True, nullable=False)
    deleted_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    
    __table_args__ = (
        Index("idx_vendor_name_normalized", "name_normalized"),
        Index("idx_vendor_token", "vendor_token"),
        Index("idx_vendor_token_hash", "vendor_token_hash"),
        Index("idx_vendor_deleted_at", "deleted_at"),
    )


# ============ WAREHOUSE HIERARCHY ============
class Warehouse(Base):
    __tablename__ = "warehouses"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    address = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    
    zones = relationship("WarehouseZone", back_populates="warehouse", cascade="all, delete-orphan", lazy="selectin")


class WarehouseZone(Base):
    __tablename__ = "warehouse_zones"
    
    id = Column(Integer, primary_key=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    
    warehouse = relationship("Warehouse", back_populates="zones")
    racks = relationship("WarehouseRack", back_populates="zone", cascade="all, delete-orphan", lazy="selectin")


class WarehouseRack(Base):
    __tablename__ = "warehouse_racks"
    
    id = Column(Integer, primary_key=True)
    zone_id = Column(Integer, ForeignKey("warehouse_zones.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    
    zone = relationship("WarehouseZone", back_populates="racks")
    shelves = relationship("WarehouseShelf", back_populates="rack", cascade="all, delete-orphan", lazy="selectin")


class WarehouseShelf(Base):
    __tablename__ = "warehouse_shelves"
    
    id = Column(Integer, primary_key=True)
    rack_id = Column(Integer, ForeignKey("warehouse_racks.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    
    rack = relationship("WarehouseRack", back_populates="shelves")
    bins = relationship("WarehouseBin", back_populates="shelf", cascade="all, delete-orphan", lazy="selectin")


class WarehouseBin(Base):
    __tablename__ = "warehouse_bins"
    
    id = Column(Integer, primary_key=True)
    shelf_id = Column(Integer, ForeignKey("warehouse_shelves.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    
    shelf = relationship("WarehouseShelf", back_populates="bins")
    inventory_items = relationship("InventoryItem", back_populates="bin")


# ============ INVENTORY ============
class InventoryCategory(Base):
    __tablename__ = "inventory_categories"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    parent_id = Column(Integer, ForeignKey("inventory_categories.id"))
    
    items = relationship("InventoryItem", back_populates="category")


class InventoryItem(Base):
    __tablename__ = "inventory_items"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    sku = Column(String(100), unique=True, nullable=False)
    barcode = Column(String(100), unique=True, nullable=True)
    qr_code_data = Column(String(255))
    category_id = Column(Integer, ForeignKey("inventory_categories.id"))
    item_type = Column(String(20), nullable=False, default="consumable")  # consumable | returnable
    current_quantity = Column(Numeric(12, 2), default=0, nullable=False)
    reserved_quantity = Column(Numeric(12, 2), default=0, nullable=False)
    minimum_quantity = Column(Numeric(12, 2), default=0, nullable=False)
    bin_id = Column(Integer, ForeignKey("warehouse_bins.id"))
    description = Column(Text)
    image_url = Column(String(500))
    is_active = Column(Boolean, default=True, nullable=False)
    deleted_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    
    category = relationship("InventoryCategory", back_populates="items")
    bin = relationship("WarehouseBin", back_populates="inventory_items")
    transactions = relationship("InventoryTransaction", back_populates="item")
    
    __table_args__ = (
        Index("idx_inventory_sku", "sku"),
        Index("idx_inventory_barcode", "barcode"),
        Index("idx_inventory_category", "category_id"),
        Index("idx_inventory_deleted_at", "deleted_at"),
        Index("idx_inventory_low_stock", "current_quantity", "minimum_quantity"),
    )


# ============ TRANSACTION LEDGER ============
class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"
    
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=False)
    transaction_type = Column(String(30), nullable=False)  # opening_balance | stock_added | dispatch | adjustment | correction | return | transfer_out | transfer_in
    previous_quantity = Column(Numeric(12, 2), nullable=False)
    change_quantity = Column(Numeric(12, 2), nullable=False)
    new_quantity = Column(Numeric(12, 2), nullable=False)
    reference_type = Column(String(30))  # restock | order | return | transfer
    reference_id = Column(Integer)
    reason = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    
    item = relationship("InventoryItem", back_populates="transactions")
    user = relationship("User")
    
    __table_args__ = (
        Index("idx_txn_item", "item_id"),
        Index("idx_txn_created_at", "created_at"),
    )


# ============ AUDIT LOG ============
class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(100), nullable=False)  # login | inventory.create | inventory.edit | ...
    entity_type = Column(String(50))
    entity_id = Column(Integer)
    ip_address = Column(String(45))
    previous_value = Column(JSON)
    new_value = Column(JSON)
    reason = Column(Text)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    
    user = relationship("User")
    
    __table_args__ = (
        Index("idx_audit_user", "user_id"),
        Index("idx_audit_created_at", "created_at"),
    )


# ============ PHASE 2: ORDERS + RESERVATION + APPROVAL MATRIX ============
class ApprovalRule(Base):
    __tablename__ = "approval_rules"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    rule_type = Column(String(20), nullable=False)  # quantity | value | department | user
    condition_json = Column(JSON, nullable=False)  # {"min_quantity": 500} or {"department": "Marketing"}
    approver_role_id = Column(Integer, ForeignKey("roles.id"))
    approver_user_id = Column(Integer, ForeignKey("users.id"))
    priority = Column(Integer, default=0, nullable=False)  # lower evaluates first
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    
    approver_role = relationship("Role")
    approver_user = relationship("User")


class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True)
    order_number = Column(String(50), unique=True, nullable=False)  # format from settings.order_number_format
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    status = Column(String(30), nullable=False, default="draft")  # draft | pending_requisition | signed_requisition_uploaded | approved | dispatched | delivered | closed | cancelled
    remarks = Column(Text)
    delivery_address = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    deleted_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    
    vendor = relationship("Vendor")
    creator = relationship("User", foreign_keys=[created_by])
    approver = relationship("User", foreign_keys=[approver_id])
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    timeline_entries = relationship("OrderTimeline", back_populates="order", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_orders_vendor", "vendor_id"),
        Index("idx_orders_status", "status"),
        Index("idx_orders_created_at", "created_at"),
        Index("idx_orders_deleted_at", "deleted_at"),
        Index("idx_orders_vendor_deleted", "vendor_id", "deleted_at"),
        Index("idx_orders_status_deleted", "status", "deleted_at"),
    )


class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    title = Column(String(200), nullable=False)
    message = Column(Text)
    type = Column(String(50), default="info")
    related_entity_type = Column(String(50))
    related_entity_id = Column(Integer)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    
    user = relationship("User", foreign_keys=[user_id])
    actor = relationship("User", foreign_keys=[actor_id])
    
    __table_args__ = (
        Index("idx_notifications_user", "user_id"),
        Index("idx_notifications_unread", "user_id", "is_read"),
    )


class OrderItem(Base):
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=False)
    quantity_ordered = Column(Numeric(12, 2), nullable=False)
    quantity_reserved = Column(Numeric(12, 2), default=0, nullable=False)
    quantity_dispatched = Column(Numeric(12, 2), default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    
    order = relationship("Order", back_populates="items")
    item = relationship("InventoryItem")
    
    __table_args__ = (
        Index("idx_order_items_order", "order_id"),
    )


class OrderTimeline(Base):
    __tablename__ = "order_timeline"
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(50), nullable=False)  # created | requisition_generated | requisition_regenerated | signed_uploaded | approved | dispatched | delivered | closed | cancelled | reopened | comment
    comments = Column(Text)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    
    order = relationship("Order", back_populates="timeline_entries")
    user = relationship("User")
    
    __table_args__ = (
        Index("idx_timeline_order", "order_id"),
    )


# ============ PHASE 3: DOCUMENTS + REQUISITION PDF + SIGNATURE WORKFLOW ============
class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"))
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)  # pdf | jpg | png | docx | xlsx
    storage_path = Column(String(500), nullable=False)  # local path now, S3 key later
    doc_category = Column(String(50))  # requisition | signed_requisition | delivery_challan | invoice | approval_letter | proof_of_delivery | other
    version = Column(Integer, default=1, nullable=False)
    parent_document_id = Column(Integer, ForeignKey("documents.id"))  # version chain
    version_status = Column(String(20), default="current", nullable=False)  # current | superseded
    notes = Column(Text)
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    uploaded_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    
    order = relationship("Order")
    uploader = relationship("User")
    parent_document = relationship("Document", remote_side=[id])
    
    __table_args__ = (
        Index("idx_documents_order", "order_id"),
        Index("idx_docs_order_category_status", "order_id", "doc_category", "version_status"),
    )


# ============ PHASE 4: EMAIL DELIVERY + VENDOR PORTAL ============
class EmailTemplate(Base):
    __tablename__ = "email_templates"
    
    id = Column(Integer, primary_key=True)
    template_key = Column(String(50), unique=True, nullable=False)  # requisition_created | order_approved | order_dispatched | order_delivered | order_cancelled
    subject = Column(String(255), nullable=False)
    body_html = Column(Text, nullable=False)  # Jinja2 template
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)


class EmailLog(Base):
    __tablename__ = "email_logs"
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"))
    vendor_id = Column(Integer, ForeignKey("vendors.id", ondelete="CASCADE"))
    recipient_email = Column(String(150), nullable=False)
    template_key = Column(String(50))  # which template was used
    subject = Column(String(255), nullable=False)
    body_preview = Column(Text)  # first 500 chars for logging
    status = Column(String(20), nullable=False)  # sent | failed | bounced | opened
    send_attempts = Column(Integer, default=1, nullable=False)
    last_error = Column(Text)  # error message if failed
    sent_at = Column(DateTime(timezone=True))
    bounced_at = Column(DateTime(timezone=True))
    opened_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    
    order = relationship("Order")
    vendor = relationship("Vendor")
    
    __table_args__ = (
        Index("idx_email_log_order", "order_id"),
        Index("idx_email_log_vendor", "vendor_id"),
        Index("idx_email_log_status", "status"),
        Index("idx_email_log_created_at", "created_at"),
    )


# ============ PHASE 6: ANALYTICS + REPORTING ============
class Report(Base):
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    report_type = Column(String(50), nullable=False)  # orders | inventory | vendors | users | custom
    filters = Column(JSON)  # {status: "approved", date_from: "2026-01-01", ...}
    format = Column(String(20), nullable=False)  # csv | pdf | excel
    file_path = Column(String(500))  # path to generated file
    file_size = Column(Integer)  # bytes
    generated_at = Column(DateTime(timezone=True))
    generated_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    
    generator = relationship("User")
    
    __table_args__ = (
        Index("idx_report_type", "report_type"),
        Index("idx_report_created_at", "created_at"),
    )


class ScheduledReport(Base):
    __tablename__ = "scheduled_reports"
    
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    report_type = Column(String(50), nullable=False)
    filters = Column(JSON)
    format = Column(String(20), nullable=False)
    schedule = Column(String(50), nullable=False)  # weekly | monthly | daily
    schedule_day = Column(String(20))  # monday, 1st, daily
    email_recipients = Column(JSON)  # ["admin@company.com", ...]
    is_active = Column(Boolean, default=True, nullable=False)
    last_generated_at = Column(DateTime(timezone=True))
    next_run_at = Column(DateTime(timezone=True))
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    
    creator = relationship("User")
    
    __table_args__ = (
        Index("idx_scheduled_report_active", "is_active"),
        Index("idx_scheduled_report_next_run", "next_run_at"),
    )


class DashboardMetric(Base):
    __tablename__ = "dashboard_metrics"
    
    id = Column(Integer, primary_key=True)
    metric_type = Column(String(50), nullable=False)  # total_orders | pending_approvals | low_stock_items | etc
    metric_value = Column(String(255), nullable=False)  # Can be number, percentage, or text
    metric_metadata = Column(JSON)  # Additional data for the metric
    calculated_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    
    __table_args__ = (
        Index("idx_dashboard_metric_type", "metric_type"),
        Index("idx_dashboard_metric_calculated_at", "calculated_at"),
    )
