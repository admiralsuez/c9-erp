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


class AnalyticsReportMixin:
    """Analytics report generation."""

    def generate_analytics_report(
        self,
        analytics_data: Dict,
        include_charts: bool = True
    ) -> bytes:
        """
        Generate comprehensive analytics report PDF.
        
        Args:
            analytics_data: Complete analytics dictionary
            include_charts: Whether to include chart information
            
        Returns:
            PDF as bytes
        """
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
            from reportlab.lib import colors
        except ImportError:
            return self._generate_stub_pdf("Analytics Report")
        
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, rightMargin=0.5*inch, leftMargin=0.5*inch)
        
        story = []
        
        # Header
        story.append(self._build_header(f"{self.company_name} - Analytics Report"))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", self._small_style()))
        story.append(Spacer(1, 0.2*inch))
        
        # Order Metrics Section
        if 'order_metrics' in analytics_data:
            story.append(Paragraph("Order Metrics", self._section_title_style()))
            order_stats = analytics_data['order_metrics']
            order_summary = {
                "Total Orders": order_stats.get('total_orders', 0),
                "Pending Approvals": order_stats.get('pending_approvals', 0),
                "Avg Approval Time (days)": order_stats.get('average_approval_time_days', 0),
                "Avg Dispatch Time (days)": order_stats.get('average_dispatch_time_days', 0),
            }
            story.extend(self._build_summary_section(order_summary))
            story.append(Spacer(1, 0.1*inch))
        
        # Inventory Health Section
        if 'inventory_health' in analytics_data:
            story.append(PageBreak())
            story.append(Paragraph("Inventory Health", self._section_title_style()))
            inv_health = analytics_data['inventory_health']
            inv_summary = {
                "Total Items": inv_health.get('total_items', 0),
                "Low Stock Count": inv_health.get('low_stock_count', 0),
                "Total Quantity": inv_health.get('total_quantity', 0),
            }
            story.extend(self._build_summary_section(inv_summary))
            
            # Low stock items table
            if inv_health.get('low_stock_items'):
                story.append(Paragraph("Low Stock Items", self._subsection_style()))
                story.extend(self._build_low_stock_table(inv_health['low_stock_items']))
            story.append(Spacer(1, 0.1*inch))
        
        # Vendor Performance Section
        if 'vendor_performance' in analytics_data:
            story.append(PageBreak())
            story.append(Paragraph("Vendor Performance", self._section_title_style()))
            story.extend(self._build_vendor_table(analytics_data['vendor_performance']))
            story.append(Spacer(1, 0.1*inch))
        
        # Email Stats Section
        if 'email_stats' in analytics_data:
            story.append(PageBreak())
            story.append(Paragraph("Email Statistics", self._section_title_style()))
            email_stats = analytics_data['email_stats']
            email_summary = {
                "Total Emails Sent": email_stats.get('total_emails', 0),
                "Successful": email_stats.get('sent_count', 0),
                "Failed": email_stats.get('failed_count', 0),
                "Period (days)": email_stats.get('period_days', 0),
            }
            story.extend(self._build_summary_section(email_summary))
            story.append(Spacer(1, 0.1*inch))
        
        # User Activity Section
        if 'user_activity' in analytics_data:
            story.append(PageBreak())
            story.append(Paragraph("User Activity", self._section_title_style()))
            user_activity = analytics_data['user_activity']
            user_summary = {
                "Active Users": user_activity.get('active_users', 0),
                "Total Actions": user_activity.get('total_actions', 0),
                "Orders Created": user_activity.get('orders_created', 0),
                "Period (days)": user_activity.get('period_days', 0),
            }
            story.extend(self._build_summary_section(user_summary))
            story.append(Spacer(1, 0.1*inch))
        
        # Footer
        story.append(Spacer(1, 0.3*inch))
        footer_text = f"This is a confidential report generated by {self.company_name}"
        story.append(Paragraph(footer_text, self._footer_style()))
        
        # Build PDF
        try:
            doc.build(story)
        except Exception as e:
            logger.warning(f"PDF build failed with error {e}, generating stub PDF")
            return self._generate_stub_pdf(f"{self.company_name} - Analytics Report")
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()

    def _build_low_stock_table(self, items: List[Dict]):
        """Build low stock items table."""
        from reportlab.platypus import Spacer, Table, TableStyle
        
        story = [Spacer(1, 0.1*inch)]
        
        data = [["SKU", "Item Name", "Current", "Minimum"]]
        for item in items:
            data.append([
                str(item.get('sku', '')),
                str(item.get('name', '')),
                f"{float(item.get('current', 0)):,.0f}",
                f"{float(item.get('minimum', 0)):,.0f}",
            ])
        
        table = Table(data, colWidths=[1*self.inch, 2*self.inch, 1.2*self.inch, 1.2*self.inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.orange),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 0.2*inch))
        return story
