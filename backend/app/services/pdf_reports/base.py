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


class PDFReportBaseMixin:
    """Shared state, styles and helpers for PDF report generation."""

    def __init__(self, company_name: str = "Cloud9 ERP"):
        self.company_name = company_name
        self.pagesize = letter
        self.inch = inch

    def _build_header(self, title: str):
        """Build report header."""
        from reportlab.platypus import Spacer
        header = Paragraph(title, self._header_style())
        return [header, Spacer(1, 0.2*self.inch)]

    def _build_summary_section(self, summary_dict: Dict):
        """Build summary statistics section."""
        from reportlab.platypus import Spacer, Table, TableStyle
        
        story = []
        
        # Convert summary dict to table
        data = [["Metric", "Value"]]
        for key, value in summary_dict.items():
            if isinstance(value, (int, float)):
                value_str = f"{value:,.2f}" if isinstance(value, float) else f"{value:,}"
            else:
                value_str = str(value)
            data.append([key, value_str])
        
        try:
            table = Table(data, colWidths=[3*self.inch, 2*self.inch])
        except Exception as e:
            # Fallback if reportlab version incompatibility
            logger.debug(f"Table width error, using fallback: {str(e)}")
            from reportlab.lib.units import inch as report_inch
            table = Table(data, colWidths=[3*report_inch, 2*report_inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 0.2*inch))
        return story

    def _header_style(self):
        """Header style."""
        try:
            from reportlab.lib.styles import ParagraphStyle
            from reportlab.lib.enums import TA_CENTER
            return ParagraphStyle(
                'Header',
                fontSize=18,
                textColor=colors.black,
                alignment=TA_CENTER,
                spaceAfter=6,
                fontName='Helvetica-Bold'
            )
        except Exception as e:
            logger.error(f"Failed to create header style: {str(e)}")
            return None

    def _section_title_style(self):
        """Section title style."""
        try:
            from reportlab.lib.styles import ParagraphStyle
            from reportlab.lib.enums import TA_LEFT
            return ParagraphStyle(
                'SectionTitle',
                fontSize=13,
                textColor=colors.black,
                alignment=TA_LEFT,
                spaceAfter=6,
                fontName='Helvetica-Bold'
            )
        except Exception as e:
            logger.error(f"Failed to create section title style: {str(e)}")
            return None

    def _subsection_style(self):
        """Subsection style."""
        try:
            from reportlab.lib.styles import ParagraphStyle
            from reportlab.lib.enums import TA_LEFT
            return ParagraphStyle(
                'SubSection',
                fontSize=11,
                textColor=colors.black,
                alignment=TA_LEFT,
                spaceAfter=4,
                fontName='Helvetica-Bold'
            )
        except Exception as e:
            logger.error(f"Failed to create subsection style: {str(e)}")
            return None

    def _small_style(self):
        """Small text style."""
        try:
            from reportlab.lib.styles import ParagraphStyle
            from reportlab.lib.enums import TA_LEFT
            return ParagraphStyle(
                'Small',
                fontSize=9,
                textColor=colors.black,
                alignment=TA_LEFT,
                spaceAfter=4,
            )
        except Exception as e:
            logger.error(f"Failed to create small style: {str(e)}")
            return None

    def _footer_style(self):
        """Footer style."""
        try:
            from reportlab.lib.styles import ParagraphStyle
            from reportlab.lib.enums import TA_CENTER
            return ParagraphStyle(
                'Footer',
                fontSize=8,
                textColor=colors.grey,
                alignment=TA_CENTER,
                spaceAfter=4,
            )
        except Exception as e:
            logger.error(f"Failed to create footer style: {str(e)}")
            return None

    def _generate_stub_pdf(self, title: str) -> bytes:
        """Generate stub PDF for testing."""
        pdf_content = f"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 100 >>
stream
BT
/F1 12 Tf
50 750 Td
({title}) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000214 00000 n 
trailer
<< /Size 5 /Root 1 0 R >>
startxref
362
%%EOF""".encode()
        return pdf_content
