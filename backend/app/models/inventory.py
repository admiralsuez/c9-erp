from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Numeric, JSON, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

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
    erp_number = Column(String(100), unique=True, nullable=True)
    barcode = Column(String(100), unique=True, nullable=True)
    qr_code_data = Column(String(255))
    category_id = Column(Integer, ForeignKey("inventory_categories.id"))
    parent_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=True)
    item_type = Column(String(20), nullable=False, default="consumable")  # consumable | returnable
    current_quantity = Column(Numeric(12, 2), default=0, nullable=False)
    reserved_quantity = Column(Numeric(12, 2), default=0, nullable=False)
    minimum_quantity = Column(Numeric(12, 2), default=0, nullable=False)
    bin_id = Column(Integer, ForeignKey("warehouse_bins.id"))
    description = Column(Text)
    image_url = Column(String(500))
    is_container = Column(Boolean, default=False, nullable=False)
    is_draft = Column(Boolean, default=False, nullable=False)  # Draft status for unpublished items
    is_active = Column(Boolean, default=True, nullable=False)
    expiry_date = Column(DateTime(timezone=True), nullable=True)  # Optional expiry date for perishables
    allow_no_expiry = Column(Boolean, default=True, nullable=False)  # Allow items without expiry
    stock_status = Column(String(50), default="active", nullable=False)  # active | expired | damaged
    deleted_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    
    category = relationship("InventoryCategory", back_populates="items")
    bin = relationship("WarehouseBin", back_populates="inventory_items")
    transactions = relationship("InventoryTransaction", back_populates="item")
    images = relationship("InventoryItemImage", back_populates="item", cascade="all, delete-orphan")
    serial_numbers = relationship("SerialNumber", back_populates="item", cascade="all, delete-orphan")
    attributes = relationship("InventoryItemAttribute", back_populates="item", cascade="all, delete-orphan")
    parent = relationship("InventoryItem", remote_side=[id], back_populates="children")
    children = relationship("InventoryItem", back_populates="parent", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_inventory_sku", "sku"),
        Index("idx_inventory_barcode", "barcode"),
        Index("idx_inventory_category", "category_id"),
        Index("idx_inventory_parent", "parent_id"),
        Index("idx_inventory_deleted_at", "deleted_at"),
        Index("idx_inventory_is_draft", "is_draft"),
        Index("idx_inventory_low_stock", "current_quantity", "minimum_quantity"),
        UniqueConstraint("sku", name="uq_inventory_sku"),
    )

    def _latest_image_url(self, image_type: str):
        """Return the most recent image URL of the given type, or None."""
        imgs = [img for img in self.images if img.image_type == image_type]
        if not imgs:
            return None
        return max(imgs, key=lambda i: i.id).image_url

    @property
    def front_image_url(self):
        return self._latest_image_url("front")

    @property
    def back_image_url(self):
        return self._latest_image_url("back")


class InventoryItemAttribute(Base):
    __tablename__ = "inventory_item_attributes"
    
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False)
    attribute_name = Column(String(100), nullable=False)
    attribute_value = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    
    item = relationship("InventoryItem", back_populates="attributes")
    
    __table_args__ = (
        UniqueConstraint("item_id", "attribute_name", name="uq_item_attribute"),
        Index("idx_item_attr_name", "attribute_name"),
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


# ============ INVENTORY ITEM IMAGES ============
class InventoryItemImage(Base):
    __tablename__ = "inventory_item_images"
    
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False)
    image_type = Column(String(20), nullable=False)  # "front" | "back"
    image_url = Column(String(500), nullable=False)  # DigitalOcean Spaces URL
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    uploaded_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    
    item = relationship("InventoryItem", back_populates="images")
    uploader = relationship("User")
    
    __table_args__ = (
        Index("idx_item_image_item", "item_id"),
        Index("idx_item_image_type", "image_type"),
    )


# ============ SERIAL NUMBERS ============
class SerialNumber(Base):
    __tablename__ = "serial_numbers"
    
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False)
    serial_number = Column(String(255), nullable=False)  # e.g., "FRIDGE-001-SN001" or "RB-200"
    batch_id = Column(String(100))  # e.g., "RB-2024-BATCH1" for ranges
    unit_condition = Column(String(30), default="new")  # "new" | "used" | "damaged" | "refurbished"
    location_bin_id = Column(Integer, ForeignKey("warehouse_bins.id"))  # Where this specific unit is stored
    assigned_to_order_id = Column(Integer, ForeignKey("orders.id"))  # null if in stock, populated if dispatched
    notes = Column(Text)  # Additional notes about this unit
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    
    item = relationship("InventoryItem", back_populates="serial_numbers")
    location_bin = relationship("WarehouseBin")
    assigned_order = relationship("Order")
    
    __table_args__ = (
        Index("idx_serial_item", "item_id"),
        Index("idx_serial_number", "serial_number"),
        Index("idx_serial_batch", "batch_id"),
        Index("idx_serial_order", "assigned_to_order_id"),
        Index("idx_serial_condition", "unit_condition"),
    )

