"""
Helper service to send order-related emails.
"""

import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.models import Order, EmailTemplate, EmailLog, Document
from app.services.email_service import get_email_service
from app.services.storage import get_storage_backend
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)


def send_order_email(
    db: Session,
    order: Order,
    template_key: str,
    context: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Send a templated email for an order.
    
    Args:
        db: Database session
        order: Order object
        template_key: Email template key (requisition_created, order_approved, etc.)
        context: Additional context variables for template rendering
        
    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        # Get recipient email
        recipient_email = order.vendor.email_contact or order.vendor.email
        if not recipient_email:
            logger.warning(f"Order {order.id}: No recipient email for vendor {order.vendor.id}")
            return False
        
        # Get email template
        template = db.query(EmailTemplate).filter(
            EmailTemplate.template_key == template_key,
            EmailTemplate.is_active == True
        ).first()
        
        if not template:
            logger.warning(f"Order {order.id}: Email template '{template_key}' not found or inactive")
            return False
        
        # Build context
        from app.models import Settings
        settings = db.query(Settings).first()
        company_name = settings.company_name if settings else "Cloud9 ERP"
        
        email_context = {
            "order": order,
            "vendor": order.vendor,
            "company_name": company_name,
            "requested_by": order.creator.full_name if order.creator else "System",
            "portal_url": "https://cloud9erp.com/vendor/portal",
        }
        
        # Add items with details
        email_context["items"] = [
            {
                "sku": item.item.sku,
                "name": item.item.name,
                "quantity_ordered": str(item.quantity_ordered),
                "quantity_dispatched": str(item.quantity_dispatched),
                "quantity_reserved": str(item.quantity_reserved),
            }
            for item in order.items
        ]
        
        # Merge custom context
        if context:
            email_context.update(context)
        
        # Get attachments if this is requisition_created
        attachments = None
        if template_key == "requisition_created":
            attachments = _get_requisition_attachments(db, order)
        
        # Send email
        email_service = get_email_service()
        success = email_service.send_templated_email(
            to_email=recipient_email,
            template=template,
            context=email_context,
            attachments=attachments
        )
        
        # Log email in database
        try:
            email_log = EmailLog(
                order_id=order.id,
                vendor_id=order.vendor_id,
                recipient_email=recipient_email,
                template_key=template_key,
                subject=template.subject,
                body_preview=template.body_html[:500],  # First 500 chars
                status="sent" if success else "failed",
                sent_at=datetime.now(timezone.utc) if success else None
            )
            db.add(email_log)
            db.flush()
        except Exception as e:
            logger.error(f"Failed to log email for order {order.id}: {str(e)}")
        
        if success:
            logger.info(f"Order {order.id}: Email '{template_key}' sent to {recipient_email}")
        else:
            logger.error(f"Order {order.id}: Failed to send email '{template_key}' to {recipient_email}")
        
        return success
        
    except Exception as e:
        logger.error(f"Order email send error: {str(e)}")
        return False


def send_requisition_created_email(db: Session, order: Order) -> bool:
    """Send requisition_created email when order is submitted."""
    return send_order_email(db, order, "requisition_created")


def send_order_approved_email(db: Session, order: Order, approved_by: str) -> bool:
    """Send order_approved email when order is approved."""
    context = {
        "approved_by": approved_by,
        "approved_date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
    }
    return send_order_email(db, order, "order_approved", context)


def send_order_dispatched_email(db: Session, order: Order, dispatch_date: str = None) -> bool:
    """Send order_dispatched email when order is dispatched."""
    context = {
        "dispatch_date": dispatch_date or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "expected_delivery_date": datetime.fromtimestamp(datetime.now(timezone.utc).timestamp() + 7 * 24 * 3600, tz=timezone.utc).strftime('%Y-%m-%d'),  # 7 days estimate
    }
    return send_order_email(db, order, "order_dispatched", context)


def send_order_delivered_email(db: Session, order: Order, delivery_date: str = None) -> bool:
    """Send order_delivered email when order is delivered."""
    context = {
        "delivery_date": delivery_date or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }
    return send_order_email(db, order, "order_delivered", context)


def send_order_cancelled_email(db: Session, order: Order, reason: str, cancelled_by: str) -> bool:
    """Send order_cancelled email when order is cancelled."""
    context = {
        "cancellation_reason": reason or "No reason provided",
        "cancellation_date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "cancelled_by": cancelled_by,
    }
    return send_order_email(db, order, "order_cancelled", context)


def _get_requisition_attachments(db: Session, order: Order):
    """Get requisition PDF documents as attachments."""
    attachments = []
    
    try:
        # Get current requisition documents
        docs = db.query(Document).filter(
            Document.order_id == order.id,
            Document.doc_category == "requisition",
            Document.version_status == "current"
        ).all()
        
        storage = get_storage_backend()
        
        for doc in docs:
            content = storage.read(doc.storage_path)
            if content:
                attachments.append({
                    "filename": doc.file_name,
                    "content": content,
                    "mimetype": f"application/{doc.file_type}"
                })
                logger.info(f"Attached document {doc.file_name} to email for order {order.id}")
        
    except Exception as e:
        logger.warning(f"Failed to attach documents for order {order.id}: {str(e)}")
    
    return attachments if attachments else None
