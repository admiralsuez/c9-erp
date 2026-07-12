"""
PDF generation service for requisition documents with company branding and QR codes.
"""

import logging
from io import BytesIO
from datetime import datetime
from typing import Optional
from decimal import Decimal
import qrcode

logger = logging.getLogger(__name__)

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
except ImportError:
    # reportlab not installed - provide stub for testing
    pass


class PDFGenerator:
    """Generate PDF requisition documents."""
    
    def __init__(self, company_name: str = "Cloud9", logo_url: Optional[str] = None):
        """
        Initialize PDF generator.
        
        Args:
            company_name: Company name for header
            logo_url: URL or path to company logo
        """
        self.company_name = company_name
        self.logo_url = logo_url
    
    def generate_requisition(
        self,
        order_number: str,
        vendor_name: str,
        vendor_address: str,
        items: list,
        remarks: str = "",
        delivery_address: str = "",
        requested_by: str = "",
        company_address: str = "",
        order_url: str = "",
        header_text: str = "",
        footer_text: str = "",
        approver_name: str = "",
        approver_signature_base64: str = ""
    ) -> bytes:
        """
        Generate a requisition PDF.
        
        Args:
            order_number: Order number
            vendor_name: Vendor name
            vendor_address: Vendor address
            items: List of dicts with {name, sku, quantity, description}
            remarks: Order remarks
            delivery_address: Delivery address
            requested_by: Name of requesting user
            company_address: Company address
            order_url: URL to order detail page (for QR code)
            header_text: Header text from settings
            footer_text: Footer text from settings
            approver_name: Name of approver (for signed PDF)
            approver_signature_base64: Base64-encoded signature image (for signed PDF)
            
        Returns:
            PDF as bytes
        """
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        except ImportError:
            # Fallback: return empty PDF-like response for testing without reportlab
            return self._generate_stub_pdf(order_number)
        
        # Create PDF in memory
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, rightMargin=0.4*inch, leftMargin=0.4*inch)
        
        story = []
        
        # Header with company info
        story.append(Paragraph(f"<b>{self.company_name}</b>", self._header_style()))
        story.append(Paragraph(company_address, self._small_style()))
        story.append(Spacer(1, 0.1*inch))
        
        if header_text:
            story.append(Paragraph(header_text, self._small_style()))
            story.append(Spacer(1, 0.05*inch))
        
        # Title
        story.append(Paragraph("PURCHASE REQUISITION", self._title_style()))
        story.append(Spacer(1, 0.1*inch))
        
        # Order details + Vendor info in a compact layout
        details_data = [
            ["Order #:", order_number, "Date:", datetime.now().strftime("%Y-%m-%d")],
            ["Vendor:", vendor_name, "Requested By:", requested_by],
        ]
        details_table = Table(details_data, colWidths=[1*inch, 2.5*inch, 1*inch, 2.5*inch])
        details_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(details_table)
        story.append(Spacer(1, 0.1*inch))
        
        # Items table
        story.append(Paragraph("<b>Items</b>", self._body_style()))
        items_data = [["#", "SKU / Description", "Qty"]]
        for idx, item in enumerate(items, 1):
            desc = str(item.get("name", ""))
            sku = str(item.get("sku", ""))
            if sku:
                desc = f"{sku} - {desc}"
            items_data.append([
                str(idx),
                desc,
                str(item.get("quantity", ""))
            ])
        
        items_table = Table(items_data, colWidths=[0.4*inch, 4.3*inch, 1*inch])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (2, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ]))
        story.append(items_table)
        story.append(Spacer(1, 0.08*inch))
        
        # Remarks / Delivery / QR side by side
        right_col = []
        if remarks:
            right_col.append(Paragraph(f"<b>Remarks:</b> {remarks}", self._small_style()))
        if delivery_address:
            right_col.append(Spacer(1, 0.05*inch))
            right_col.append(Paragraph(f"<b>Delivery Address:</b> {delivery_address}", self._small_style()))
        
        if order_url:
            try:
                qr = qrcode.QRCode(version=1, box_size=8, border=4)
                qr.add_data(order_url)
                qr.make(fit=True)
                qr_img = qr.make_image(fill_color="black", back_color="white")
                qr_buffer = BytesIO()
                qr_img.save(qr_buffer, format="PNG")
                qr_buffer.seek(0)
                from reportlab.platypus import Image as RLImage
                qr_image = RLImage(qr_buffer, width=0.7*inch, height=0.7*inch)
            except Exception:
                qr_image = None
            
            if right_col:
                qr_align = [qr_image, Spacer(1, 0.05*inch), Paragraph("<b>QR</b>", self._small_style())] if qr_image else []
                if qr_align:
                    story.append(Spacer(1, 0.05*inch))
                    qr_table = Table([[qr_align, right_col]], colWidths=[1*inch, 5.7*inch])
                    qr_table.setStyle(TableStyle([
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ]))
                    story.append(qr_table)
                else:
                    for item in right_col:
                        story.append(item)
            else:
                if qr_image:
                    story.append(Spacer(1, 0.05*inch))
                    story.append(Paragraph("<b>Order QR Code</b>", self._small_style()))
                    story.append(qr_image)
        else:
            for item in right_col:
                story.append(item)
        
        story.append(Spacer(1, 0.08*inch))
        story.append(Paragraph("<b>Approval Section</b>", self._body_style()))
        
        signature_data = [
            ["Requested By:", requested_by, f"Date: {datetime.now().strftime('%Y-%m-%d')}"],
            ["", "_____________________", ""],
        ]
        
        try:
            from reportlab.platypus import Image as RLImage
            import base64
            if approver_signature_base64:
                sig_bytes = base64.b64decode(approver_signature_base64.split(",")[-1])
                sig_buffer = BytesIO(sig_bytes)
                sig_image = RLImage(sig_buffer, width=2*inch, height=0.5*inch)
                signature_data.append(["Approved By:", approver_name, f"Date: {datetime.now().strftime('%Y-%m-%d')}"])
                signature_data.append(["", sig_image, ""])
            else:
                signature_data.append(["Approved By:", "_____________________", f"Date: __________"])
                signature_data.append(["", "Signature", ""])
        except Exception:
            signature_data.append(["Approved By:", "_____________________", f"Date: __________"])
            signature_data.append(["", "Signature", ""])
        
        signature_data.append(["", "", ""])
        signature_data.append(["Received By:", "_____________________", "Date: __________"])
        signature_data.append(["", "Signature", ""])
        
        sig_table = Table(signature_data, colWidths=[1.5*inch, 2.5*inch, 1.5*inch])
        sig_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(sig_table)
        
        # Footer
        story.append(Spacer(1, 0.3*inch))
        if footer_text:
            story.append(Paragraph(footer_text, self._small_style()))
        
        # Build PDF
        doc.build(story)
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()
    
    def _header_style(self):
        """Style for document header."""
        try:
            from reportlab.lib.styles import ParagraphStyle
            from reportlab.lib.enums import TA_CENTER
            return ParagraphStyle(
                'Header',
                fontSize=16,
                textColor=colors.black,
                alignment=TA_CENTER,
                spaceAfter=6,
            )
        except Exception as e:
            logger.error("Failed to create header style: %s", str(e))
            return None
    
    def _title_style(self):
        """Style for document title."""
        try:
            from reportlab.lib.styles import ParagraphStyle
            from reportlab.lib.enums import TA_CENTER
            return ParagraphStyle(
                'Title',
                fontSize=14,
                textColor=colors.black,
                alignment=TA_CENTER,
                spaceAfter=12,
                fontName='Helvetica-Bold'
            )
        except Exception as e:
            logger.error("Failed to create title style: %s", str(e))
            return None
    
    def _body_style(self):
        """Style for body text."""
        try:
            from reportlab.lib.styles import ParagraphStyle
            from reportlab.lib.enums import TA_LEFT
            return ParagraphStyle(
                'Body',
                fontSize=11,
                textColor=colors.black,
                alignment=TA_LEFT,
                spaceAfter=6,
                fontName='Helvetica-Bold'
            )
        except Exception as e:
            logger.error("Failed to create body style: %s", str(e))
            return None
    
    def _small_style(self):
        """Style for small text."""
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
            logger.error("Failed to create small style: %s", str(e))
            return None
    
    def _generate_stub_pdf(self, order_number: str) -> bytes:
        """Generate a stub PDF when reportlab is not available."""
        # Return minimal PDF-like content for testing
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
(Requisition: {order_number}) Tj
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
