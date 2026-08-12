from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Numeric, JSON, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

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

