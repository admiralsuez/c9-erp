"""
Default email templates for order notifications.
"""

DEFAULT_EMAIL_TEMPLATES = {
    "requisition_created": {
        "subject": "Purchase Requisition #{{ order.order_number }} from {{ company_name }}",
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; color: #333;">
    <h2>Purchase Requisition Created</h2>
    <p>Dear {{ vendor.contact_person or vendor.name }},</p>
    
    <p>We have created a new purchase requisition for your company. Please find the details below:</p>
    
    <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
        <tr style="background-color: #f2f2f2;">
            <td style="border: 1px solid #ddd; padding: 8px;"><strong>Order Number</strong></td>
            <td style="border: 1px solid #ddd; padding: 8px;">{{ order.order_number }}</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 8px;"><strong>Order Date</strong></td>
            <td style="border: 1px solid #ddd; padding: 8px;">{{ order.created_at.strftime('%Y-%m-%d') }}</td>
        </tr>
        <tr style="background-color: #f2f2f2;">
            <td style="border: 1px solid #ddd; padding: 8px;"><strong>Delivery Address</strong></td>
            <td style="border: 1px solid #ddd; padding: 8px;">{{ order.delivery_address }}</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 8px;"><strong>Requested By</strong></td>
            <td style="border: 1px solid #ddd; padding: 8px;">{{ requested_by }}</td>
        </tr>
    </table>
    
    <h3>Items Ordered:</h3>
    <table style="border-collapse: collapse; width: 100%;">
        <tr style="background-color: #f2f2f2;">
            <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">SKU</th>
            <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Item</th>
            <th style="border: 1px solid #ddd; padding: 8px; text-align: right;">Quantity</th>
        </tr>
        {% for item in items %}
        <tr>
            <td style="border: 1px solid #ddd; padding: 8px;">{{ item.sku }}</td>
            <td style="border: 1px solid #ddd; padding: 8px;">{{ item.name }}</td>
            <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{{ item.quantity_ordered }}</td>
        </tr>
        {% endfor %}
    </table>
    
    {% if order.remarks %}
    <h3>Remarks:</h3>
    <p>{{ order.remarks }}</p>
    {% endif %}
    
    <p style="margin-top: 30px;">Please sign and return the attached requisition PDF. You can track your order status at: <a href="{{ portal_url }}">{{ portal_url }}</a></p>
    
    <p>Best regards,<br/>
    {{ company_name }} Procurement Team</p>
    
    <hr style="border: none; border-top: 1px solid #ddd; margin-top: 30px;">
    <p style="font-size: 12px; color: #666;">This is an automated email. Please do not reply directly. Contact procurement@company.com for questions.</p>
</body>
</html>
        """
    },
    "order_approved": {
        "subject": "Purchase Order Approved - #{{ order.order_number }}",
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; color: #333;">
    <h2>Purchase Order Approved</h2>
    <p>Dear {{ vendor.contact_person or vendor.name }},</p>
    
    <p>Your purchase requisition has been approved and is now a confirmed purchase order.</p>
    
    <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
        <tr style="background-color: #f2f2f2;">
            <td style="border: 1px solid #ddd; padding: 8px;"><strong>Order Number</strong></td>
            <td style="border: 1px solid #ddd; padding: 8px;">{{ order.order_number }}</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 8px;"><strong>Status</strong></td>
            <td style="border: 1px solid #ddd; padding: 8px;"><strong style="color: green;">APPROVED</strong></td>
        </tr>
        <tr style="background-color: #f2f2f2;">
            <td style="border: 1px solid #ddd; padding: 8px;"><strong>Approved By</strong></td>
            <td style="border: 1px solid #ddd; padding: 8px;">{{ approved_by }}</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 8px;"><strong>Approved On</strong></td>
            <td style="border: 1px solid #ddd; padding: 8px;">{{ approved_date }}</td>
        </tr>
    </table>
    
    <p>Please ensure timely delivery to the specified address. You can view the full order details and track shipment status at: <a href="{{ portal_url }}">{{ portal_url }}</a></p>
    
    <p>Best regards,<br/>
    {{ company_name }} Procurement Team</p>
</body>
</html>
        """
    },
    "order_dispatched": {
        "subject": "Order Dispatched - #{{ order.order_number }}",
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; color: #333;">
    <h2>Order Dispatched</h2>
    <p>Dear {{ vendor.contact_person or vendor.name }},</p>
    
    <p>Your order has been dispatched and is on its way. Please find the shipment details below:</p>
    
    <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
        <tr style="background-color: #f2f2f2;">
            <td style="border: 1px solid #ddd; padding: 8px;"><strong>Order Number</strong></td>
            <td style="border: 1px solid #ddd; padding: 8px;">{{ order.order_number }}</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 8px;"><strong>Dispatch Date</strong></td>
            <td style="border: 1px solid #ddd; padding: 8px;">{{ dispatch_date }}</td>
        </tr>
        <tr style="background-color: #f2f2f2;">
            <td style="border: 1px solid #ddd; padding: 8px;"><strong>Delivery Address</strong></td>
            <td style="border: 1px solid #ddd; padding: 8px;">{{ order.delivery_address }}</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 8px;"><strong>Expected Delivery</strong></td>
            <td style="border: 1px solid #ddd; padding: 8px;">{{ expected_delivery_date }}</td>
        </tr>
    </table>
    
    <h3>Items Dispatched:</h3>
    <table style="border-collapse: collapse; width: 100%;">
        <tr style="background-color: #f2f2f2;">
            <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">SKU</th>
            <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Item</th>
            <th style="border: 1px solid #ddd; padding: 8px; text-align: right;">Quantity</th>
        </tr>
        {% for item in items %}
        <tr>
            <td style="border: 1px solid #ddd; padding: 8px;">{{ item.sku }}</td>
            <td style="border: 1px solid #ddd; padding: 8px;">{{ item.name }}</td>
            <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{{ item.quantity_dispatched }}</td>
        </tr>
        {% endfor %}
    </table>
    
    <p style="margin-top: 30px;">Please keep the tracking information for your records. Track your shipment at: <a href="{{ portal_url }}">{{ portal_url }}</a></p>
    
    <p>Best regards,<br/>
    {{ company_name }} Logistics Team</p>
</body>
</html>
        """
    },
    "order_delivered": {
        "subject": "Order Delivered - #{{ order.order_number }}",
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; color: #333;">
    <h2>Order Delivered</h2>
    <p>Dear {{ vendor.contact_person or vendor.name }},</p>
    
    <p>Your order has been successfully delivered.</p>
    
    <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
        <tr style="background-color: #f2f2f2;">
            <td style="border: 1px solid #ddd; padding: 8px;"><strong>Order Number</strong></td>
            <td style="border: 1px solid #ddd; padding: 8px;">{{ order.order_number }}</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 8px;"><strong>Delivery Date</strong></td>
            <td style="border: 1px solid #ddd; padding: 8px;">{{ delivery_date }}</td>
        </tr>
        <tr style="background-color: #f2f2f2;">
            <td style="border: 1px solid #ddd; padding: 8px;"><strong>Status</strong></td>
            <td style="border: 1px solid #ddd; padding: 8px;"><strong style="color: green;">DELIVERED</strong></td>
        </tr>
    </table>
    
    <p>Thank you for your business. If you have any issues or concerns regarding this shipment, please contact us immediately at procurement@company.com.</p>
    
    <p>Best regards,<br/>
    {{ company_name }} Customer Service Team</p>
</body>
</html>
        """
    },
    "order_cancelled": {
        "subject": "Order Cancelled - #{{ order.order_number }}",
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; color: #333;">
    <h2>Order Cancelled</h2>
    <p>Dear {{ vendor.contact_person or vendor.name }},</p>
    
    <p>Your purchase order has been cancelled. Please find the details below:</p>
    
    <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
        <tr style="background-color: #f2f2f2;">
            <td style="border: 1px solid #ddd; padding: 8px;"><strong>Order Number</strong></td>
            <td style="border: 1px solid #ddd; padding: 8px;">{{ order.order_number }}</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 8px;"><strong>Cancellation Date</strong></td>
            <td style="border: 1px solid #ddd; padding: 8px;">{{ cancellation_date }}</td>
        </tr>
        <tr style="background-color: #f2f2f2;">
            <td style="border: 1px solid #ddd; padding: 8px;"><strong>Reason</strong></td>
            <td style="border: 1px solid #ddd; padding: 8px;">{{ cancellation_reason }}</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 8px;"><strong>Cancelled By</strong></td>
            <td style="border: 1px solid #ddd; padding: 8px;">{{ cancelled_by }}</td>
        </tr>
    </table>
    
    <p>If you have any questions regarding this cancellation, please contact us at procurement@company.com.</p>
    
    <p>Best regards,<br/>
    {{ company_name }} Procurement Team</p>
</body>
</html>
        """
    }
}


def get_default_templates() -> dict:
    """Get default email templates."""
    return DEFAULT_EMAIL_TEMPLATES


def init_email_templates(db):
    """Initialize default email templates in the database.
    
    Args:
        db: SQLAlchemy session
    """
    from app.models import EmailTemplate
    
    for key, template_data in DEFAULT_EMAIL_TEMPLATES.items():
        # Check if template already exists
        existing = db.query(EmailTemplate).filter(
            EmailTemplate.template_key == key
        ).first()
        
        if not existing:
            template = EmailTemplate(
                template_key=key,
                subject=template_data["subject"],
                body_html=template_data["body_html"],
                is_active=True
            )
            db.add(template)
    
    db.commit()
