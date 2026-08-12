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


class OrderReportMixin:
    """Order report generation."""

    def generate_order_report(
        self,
        orders_data: List[Dict],
        date_range: Optional[Dict] = None,
        summary_stats: Optional[Dict] = None
    ) -> bytes:
        """
        Generate orders report PDF.
        
        Args:
            orders_data: List of order dictionaries
            date_range: Optional dict with 'start' and 'end' dates
            summary_stats: Optional summary statistics dict
            
        Returns:
            PDF as bytes
        """
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
            from reportlab.lib import colors
        except ImportError:
            return self._generate_stub_pdf("Order Report")
        
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, rightMargin=0.5*inch, leftMargin=0.5*inch)
        
        story = []
        
        # Header
        story.append(self._build_header(f"{self.company_name} - Order Report"))
        
        # Date range
        if date_range:
            date_text = f"Report Period: {date_range.get('start', 'N/A')} to {date_range.get('end', 'N/A')}"
            story.append(Paragraph(date_text, self._small_style()))
            story.append(Spacer(1, 0.1*inch))
        
        # Summary statistics
        if summary_stats:
            story.extend(self._build_summary_section(summary_stats))
        
        # Orders table
        if orders_data:
            story.append(PageBreak())
            story.extend(self._build_orders_table(orders_data))
        
        # Footer
        story.append(Spacer(1, 0.3*inch))
        footer_text = f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        story.append(Paragraph(footer_text, self._footer_style()))
        
        # Build PDF
        try:
            doc.build(story)
        except Exception as e:
            logger.warning(f"PDF build failed with error {e}, generating stub PDF")
            return self._generate_stub_pdf(f"{self.company_name} - Order Report")
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()

    def _build_orders_table(self, orders: List[Dict]):
        """Build orders table."""
        from reportlab.platypus import Spacer, Table, TableStyle
        
        story = [Paragraph("Orders", self._section_title_style())]
        story.append(Spacer(1, 0.1*inch))
        
        data = [["Order #", "Vendor", "Status", "Created", "Items"]]
        for order in orders[:50]:  # Limit to 50 rows per page
            data.append([
                str(order.get('id', '')),
                str(order.get('vendor_name', '')),
                str(order.get('status', '')),
                str(order.get('created_at', ''))[:10],
                str(order.get('item_count', 0)),
            ])
        
        if len(orders) > 50:
            table = Table(data, colWidths=[1*self.inch, 1.5*self.inch, 1.2*self.inch, 1.2*self.inch, 0.8*self.inch])
        else:
            table = Table(data, colWidths=[1*self.inch, 1.5*self.inch, 1.2*self.inch, 1.2*self.inch, 0.8*self.inch])
        
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
        story.append(Spacer(1, 0.2*inch))
        return story
