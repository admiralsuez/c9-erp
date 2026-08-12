from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Numeric, JSON, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

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
    ho_prefix = Column(String(10), default="HO")
    llf_prefix = Column(String(10), default="LLF")
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

