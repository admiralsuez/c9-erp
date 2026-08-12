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


class InventoryReportMixin:
    """Inventory report generation."""

    def generate_inventory_report(
        self,
        inventory_data: List[Dict],
        summary_stats: Optional[Dict] = None
    ) -> bytes:
        """
        Generate inventory report PDF.
        
        Args:
            inventory_data: List of inventory item dictionaries
            summary_stats: Optional summary statistics
            
        Returns:
            PDF as bytes
        """
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
            from reportlab.lib import colors
        except ImportError:
            return self._generate_stub_pdf("Inventory Report")
        
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, rightMargin=0.5*inch, leftMargin=0.5*inch)
        
        story = []
        
        # Header
        story.append(self._build_header(f"{self.company_name} - Inventory Report"))
        
        # Summary
        if summary_stats:
            story.extend(self._build_summary_section(summary_stats))
        
        # Inventory table
        if inventory_data:
            story.append(PageBreak())
            story.extend(self._build_inventory_table(inventory_data))
        
        # Footer
        story.append(Spacer(1, 0.3*inch))
        footer_text = f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        story.append(Paragraph(footer_text, self._footer_style()))
        
        # Build PDF
        try:
            doc.build(story)
        except Exception as e:
            logger.warning(f"PDF build failed with error {e}, generating stub PDF")
            return self._generate_stub_pdf(f"{self.company_name} - Inventory Report")
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()

    def _build_inventory_table(self, inventory: List[Dict]):
        """Build inventory table."""
        from reportlab.platypus import Spacer, Table, TableStyle
        
        story = [Paragraph("Inventory Items", self._section_title_style())]
        story.append(Spacer(1, 0.1*inch))
        
        data = [["SKU", "Name", "Current Qty", "Minimum Qty", "Status"]]
        for item in inventory[:50]:
            current = item.get('current_quantity', 0)
            minimum = item.get('minimum_quantity', 0)
            status = "Low" if current <= minimum else "OK"
            data.append([
                str(item.get('sku', '')),
                str(item.get('name', '')),
                f"{float(current):,.0f}",
                f"{float(minimum):,.0f}",
                status,
            ])
        
        table = Table(data, colWidths=[0.9*self.inch, 1.5*self.inch, 1.2*self.inch, 1.2*self.inch, 0.8*self.inch])
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
