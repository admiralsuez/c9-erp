"""PDF report generation for the C9 ERP report suite."""

from io import BytesIO
from datetime import datetime
from typing import List, Dict, Optional
import logging

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
except ImportError:
    pass

logger = logging.getLogger(__name__)


class VendorReportMixin:
    """Vendor performance report generation."""

    def generate_vendor_report(
        self,
        vendor_data: List[Dict],
        performance_metrics: Optional[Dict] = None
    ) -> bytes:
        """
        Generate vendor performance report PDF.
        
        Args:
            vendor_data: List of vendor dictionaries
            performance_metrics: Optional performance metrics
            
        Returns:
            PDF as bytes
        """
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
            from reportlab.lib import colors
        except ImportError:
            return self._generate_stub_pdf("Vendor Report")
        
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, rightMargin=0.5*inch, leftMargin=0.5*inch)
        
        story = []
        
        # Header
        story.append(self._build_header(f"{self.company_name} - Vendor Performance Report"))
        
        # Performance metrics
        if performance_metrics:
            story.extend(self._build_summary_section(performance_metrics))
        
        # Vendor table
        if vendor_data:
            story.append(PageBreak())
            story.extend(self._build_vendor_table(vendor_data))
        
        # Footer
        story.append(Spacer(1, 0.3*inch))
        footer_text = f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        story.append(Paragraph(footer_text, self._footer_style()))
        
        # Build PDF
        try:
            doc.build(story)
        except Exception as e:
            logger.warning(f"PDF build failed with error {e}, generating stub PDF")
            return self._generate_stub_pdf(f"{self.company_name} - Vendor Report")
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()

    def _build_vendor_table(self, vendors: List[Dict]):
        """Build vendor table."""
        from reportlab.platypus import Spacer, Table, TableStyle
        
        story = [Paragraph("Vendor Data", self._subsection_style())]
        story.append(Spacer(1, 0.1*inch))
        
        data = [["Vendor Name", "Orders", "On-Time %"]]
        for vendor in vendors[:30]:
            data.append([
                str(vendor.get('vendor_name', '')),
                str(vendor.get('order_count', 0)),
                str(vendor.get('on_time_percentage', 0)) + "%",
            ])
        
        table = Table(data, colWidths=[2.5*self.inch, 1.2*self.inch, 1.2*self.inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        
        story.append(table)
        return story
