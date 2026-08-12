from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Numeric, JSON, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

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

