"""PDF report generation service.

Split from the former app/services/pdf_reports.py monolith into
domain-focused mixin modules.
"""

from app.services.pdf_reports.generator import PDFReportGenerator, get_pdf_report_generator

__all__ = [
    "PDFReportGenerator",
    "get_pdf_report_generator",
]
