"""Assembled Excel report generator."""

from app.services.excel_reports.base import ExcelReportBaseMixin
from app.services.excel_reports.orders import OrderReportMixin
from app.services.excel_reports.inventory import InventoryReportMixin
from app.services.excel_reports.vendor import VendorReportMixin
from app.services.excel_reports.analytics import AnalyticsReportMixin
from app.services.excel_reports.custom import CustomReportMixin


class ExcelReportGenerator(
    ExcelReportBaseMixin,
    OrderReportMixin,
    InventoryReportMixin,
    VendorReportMixin,
    AnalyticsReportMixin,
    CustomReportMixin,
):
    """Generate professional Excel reports with formatting and charts."""

def get_excel_report_generator() -> ExcelReportGenerator:
    """Factory function for Excel report generator."""
    return ExcelReportGenerator()
