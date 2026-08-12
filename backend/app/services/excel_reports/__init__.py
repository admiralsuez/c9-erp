"""Excel report generation service.

Split from the former app/services/excel_reports.py monolith into
domain-focused mixin modules.
"""

from app.services.excel_reports.generator import ExcelReportGenerator, get_excel_report_generator

__all__ = [
    "ExcelReportGenerator",
    "get_excel_report_generator",
]
