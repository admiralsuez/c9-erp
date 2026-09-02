from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Numeric, JSON, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


# ============ VENDOR TYPES ============
class VendorType(Base):
    __tablename__ = "vendor_types"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    
    vendors = relationship("Vendor", back_populates="vendor_type_rel", passive_deletes=True)


# ============ VENDORS ============
class Vendor(Base):
    __tablename__ = "vendors"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    name_normalized = Column(String(200), nullable=False, unique=True)
    vendor_type = Column(String(50))
    vendor_type_id = Column(Integer, ForeignKey("vendor_types.id", ondelete="SET NULL"), nullable=True)
    contact_person = Column(String(150))
    phone = Column(String(30))
    email = Column(String(150))
    email_contact = Column(String(150))  # Phase 4: distinct contact email for vendor portal
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(100))
    pincode = Column(String(10))
    gst = Column(String(20))
    notes = Column(Text)
    vendor_token = Column(String(32), unique=True)  # Phase 4: DEPRECATED - kept for migration compat
    vendor_token_hash = Column(String(64), unique=True)  # Phase 8: SHA-256 hash of vendor token
    vendor_token_expires_at = Column(DateTime(timezone=True))  # Phase 4: token expiry
    allow_portal = Column(Boolean, default=True, nullable=False)  # Phase 4: portal access flag
    parent_id = Column(Integer, ForeignKey("vendors.id", ondelete="SET NULL"), nullable=True)  # For vendor address hierarchy
    is_active = Column(Boolean, default=True, nullable=False)
    deleted_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    
    vendor_type_rel = relationship("VendorType", back_populates="vendors")
    parent = relationship("Vendor", remote_side=[id], backref="children")

    @property
    def resolved_vendor_type(self) -> str | None:
        """Return the vendor type name from the FK, falling back to the legacy string.

        Prefer this over accessing ``vendor.vendor_type`` directly when reading —
        it always returns the up-to-date value regardless of which column was last
        written. Write paths must keep the FK and the string in sync.
        """
        if self.vendor_type_rel is not None:
            return self.vendor_type_rel.name
        return self.vendor_type

    __table_args__ = (
        Index("idx_vendor_name_normalized", "name_normalized"),
        Index("idx_vendor_token", "vendor_token"),
        Index("idx_vendor_token_hash", "vendor_token_hash"),
        Index("idx_vendor_type_id", "vendor_type_id"),
        Index("idx_vendor_deleted_at", "deleted_at"),
    )

