from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Numeric, JSON, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

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
    challan_book_number = Column(String(100), nullable=True)  # Challan book number when dispatching
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
    quantity_returned = Column(Numeric(12, 2), default=0, nullable=False)
    quantity_damaged = Column(Numeric(12, 2), default=0, nullable=False)
    return_reason = Column(String(50), nullable=True)  # damaged | not_needed | null
    return_status = Column(String(50), nullable=True)  # pending | completed
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    
    order = relationship("Order", back_populates="items")
    item = relationship("InventoryItem")
    return_photos = relationship("ReturnPhoto", back_populates="order_item", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_order_items_order", "order_id"),
    )


class ReturnPhoto(Base):
    __tablename__ = "return_photos"
    
    id = Column(Integer, primary_key=True)
    order_item_id = Column(Integer, ForeignKey("order_items.id", ondelete="CASCADE"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=False)
    storage_path = Column(String(500), nullable=False)
    file_name = Column(String(255))
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    
    order_item = relationship("OrderItem", back_populates="return_photos")
    uploader = relationship("User")


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
    challan_book_number = Column(String(50), nullable=True)  # challan book number for delivery challan
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

