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


class CustomReportMixin:
    """Custom filtered report generation."""

    def generate_custom_report(self, report_data: Dict) -> bytes:
        """Generate a custom-filtered report PDF."""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
            from reportlab.lib import colors
        except ImportError:
            return self._generate_stub_pdf("Custom Report")

        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, rightMargin=0.5*inch, leftMargin=0.5*inch)
        story = []

        period = report_data.get("period", {})
        title = f"{self.company_name} - Custom Report"
        story.append(self._build_header(title))
        story.append(Paragraph(
            f"Period: {period.get('start', 'N/A')} to {period.get('end', 'N/A')} | "
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            self._small_style()
        ))
        story.append(Spacer(1, 0.2*inch))

        orders = report_data.get("orders", [])
        inventory = report_data.get("inventory", [])

        summary = {
            "Total Orders": report_data.get("total_orders", 0),
            "Total Inventory Items": report_data.get("total_items", 0),
        }
        story.extend(self._build_summary_section(summary))
        story.append(Spacer(1, 0.2*inch))

        if orders:
            story.append(PageBreak())
            story.append(Paragraph("Filtered Orders", self._section_title_style()))
            order_table_data = [["Order #", "Vendor", "Status", "Items", "Created"]]
            for o in orders[:50]:
                order_table_data.append([
                    str(o.get("order_number", "")),
                    str(o.get("vendor_name", "")),
                    str(o.get("status", "")),
                    str(o.get("item_count", 0)),
                    str(o.get("created_at", ""))[:10],
                ])
            t = Table(order_table_data, colWidths=[1.2*inch, 1.5*inch, 1.2*inch, 0.8*inch, 1.2*inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            story.append(t)

            for o in orders[:20]:
                if o.get("items"):
                    story.append(Spacer(1, 0.1*inch))
                    story.append(Paragraph(
                        f"Order {o['order_number']} items:",
                        self._subsection_style()
                    ))
                    item_data = [["SKU", "Name", "Ordered", "Dispatched"]]
                    for oi in o["items"]:
                        item_data.append([
                            str(oi.get("sku", "")),
                            str(oi.get("name", "")),
                            f"{oi.get('quantity_ordered', 0):.0f}",
                            f"{oi.get('quantity_dispatched', 0):.0f}",
                        ])
                    it = Table(item_data, colWidths=[1*inch, 1.8*inch, 0.8*inch, 0.8*inch])
                    it.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.2, 0.4, 0.6)),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('FONTSIZE', (0, 0), (-1, -1), 7),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ]))
                    story.append(it)

        if inventory:
            story.append(PageBreak())
            story.append(Paragraph("Filtered Inventory Items", self._section_title_style()))
            inv_table_data = [["SKU", "Name", "Current", "Min", "Reserved", "Category"]]
            for i in inventory:
                inv_table_data.append([
                    str(i.get("sku", "")),
                    str(i.get("name", "")),
                    f"{i.get('current_quantity', 0):.0f}",
                    f"{i.get('minimum_quantity', 0):.0f}",
                    f"{i.get('reserved_quantity', 0):.0f}",
                    str(i.get("category", "")),
                ])
            it2 = Table(inv_table_data, colWidths=[0.8*inch, 1.2*inch, 0.7*inch, 0.7*inch, 0.7*inch, 1*inch])
            it2.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTSIZE', (0, 0), (-1, -1), 7),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            story.append(it2)

        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph("Custom report generated on demand", self._footer_style()))

        try:
            doc.build(story)
        except Exception as e:
            logger.warning(f"Custom PDF build failed: {e}")
            return self._generate_stub_pdf("Custom Report")
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()
