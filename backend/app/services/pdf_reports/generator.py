"""Assembled PDF report generator."""

from app.services.pdf_reports.base import PDFReportBaseMixin
from app.services.pdf_reports.orders import OrderReportMixin
from app.services.pdf_reports.inventory import InventoryReportMixin
from app.services.pdf_reports.vendor import VendorReportMixin
from app.services.pdf_reports.analytics import AnalyticsReportMixin
from app.services.pdf_reports.custom import CustomReportMixin


class PDFReportGenerator(
    PDFReportBaseMixin,
    OrderReportMixin,
    InventoryReportMixin,
    VendorReportMixin,
    AnalyticsReportMixin,
    CustomReportMixin,
):
    """Generate professional PDF reports from analytics data."""

def get_pdf_report_generator() -> PDFReportGenerator:
    """Factory function for PDF report generator."""
    return PDFReportGenerator()
