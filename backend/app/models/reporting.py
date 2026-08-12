from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Numeric, JSON, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

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

