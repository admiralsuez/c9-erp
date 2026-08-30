import logging
import os

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, status, UploadFile
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models import Document, Order, OrderItem, OrderTimeline, Settings, User, Vendor
from app.schemas import OrderResponse
from app.services.audit_service import log_audit
from app.services.order_email_helper import send_requisition_created_email
from app.services.pdf_generator import PDFGenerator
from app.services.storage import get_storage_backend

from .orders_common import OrderStatus, add_timeline_entry

router = APIRouter(prefix="/orders", tags=["Orders"])
logger = logging.getLogger(__name__)

@router.post("/{order_id}/submit-requisition", response_model=OrderResponse)
def submit_requisition(
    order_id: int,
    approver_id: int = Query(..., description="User ID of the approver"),
    use_vendor_address: bool = Query(False, description="Use vendor address as delivery address"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Draft -> Pending Requisition with PDF generation and approver assignment."""
    order = db.query(Order).options(
        selectinload(Order.items).selectinload(OrderItem.item),
        joinedload(Order.vendor),
    ).filter(
        Order.id == order_id,
        Order.deleted_at == None
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if order.status != OrderStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition from {order.status} to pending_requisition"
        )
    
    if not order.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order must have at least one item"
        )
    
    # Validate vendor address if using vendor address as delivery address
    if use_vendor_address:
        if not order.vendor or not order.vendor.address:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vendor does not have an address. Please select a delivery address or update vendor details."
            )
        order.delivery_address = order.vendor.address
    
    # Validate approver
    approver = db.query(User).filter(
        User.id == approver_id,
        User.is_active == True,
        User.deleted_at == None
    ).first()
    if not approver:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Approver not found or inactive"
        )
    
    # Generate requisition PDF
    try:
        # Get settings for branding
        company_settings = db.query(Settings).first()
        settings_dict = {
            "company_name": company_settings.company_name if company_settings else "Cloud9",
            "company_address": company_settings.company_address if company_settings else "",
            "header_text": company_settings.pdf_header_text if company_settings else "",
            "footer_text": company_settings.pdf_footer_text if company_settings else ""
        }
        
        # Prepare items for PDF
        pdf_items = []
        for order_item in order.items:
            pdf_items.append({
                "sku": order_item.item.sku,
                "name": order_item.item.name,
                "quantity": str(order_item.quantity_ordered),
                "description": order_item.item.description or ""
            })
        
        # Generate PDF
        pdf_generator = PDFGenerator(
            company_name=settings_dict.get("company_name", "Cloud9")
        )
        
        order_url = f"http://64.227.191.1:8000/orders/{order.id}"
        pdf_content = pdf_generator.generate_requisition(
            order_number=order.order_number,
            vendor_name=order.vendor.name,
            vendor_address=order.vendor.address or "",
            items=pdf_items,
            remarks=order.remarks or "",
            delivery_address=order.delivery_address or "",
            requested_by=current_user.full_name or current_user.email,
            company_address=settings_dict.get("company_address", ""),
            order_url=order_url,
            header_text=settings_dict.get("header_text", ""),
            footer_text=settings_dict.get("footer_text", "")
        )
        
        # Save PDF to storage
        storage = get_storage_backend()
        storage_path = storage.save(
            f"orders/{order.id}/requisition.pdf",
            pdf_content
        )
        
        # Create document record
        document = Document(
            order_id=order.id,
            file_name=f"requisition_{order.order_number}.pdf",
            file_type="pdf",
            storage_path=storage_path,
            doc_category="requisition",
            version=1,
            version_status="current",
            notes="Auto-generated requisition PDF",
            uploaded_by=current_user.id
        )
        db.add(document)
        db.flush()
        
    except Exception as e:
        logger.error("PDF generation failed for order %s: %s", order.id, str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate requisition PDF: {str(e)}"
        )
    
    order.status = OrderStatus.PENDING_REQUISITION
    order.approver_id = approver.id
    add_timeline_entry(db, order, "requisition_generated", current_user)
    db.flush()
    
    # Create notification for approver
    from app.models import Notification
    notification = Notification(
        user_id=approver.id,
        actor_id=current_user.id,
        title="Requisition Pending Approval",
        message=f"Requisition {order.order_number} requires your approval.",
        type="approval",  # Changed from approval_required to approval
        related_entity_type="order",
        related_entity_id=order.id,
        is_read=False,
        is_approved=False  # Will be marked as approved when user approves
    )
    db.add(notification)
    
    log_audit(db, user_id=current_user.id, action="order.submitted", entity_type="order", entity_id=order.id)
    db.commit()
    db.refresh(order)
    
    # Send requisition created email (non-blocking)
    try:
        send_requisition_created_email(db, order)
    except Exception as e:
        logger.warning("Email send failed for order %s: %s", order.id, str(e))
    
    return order
@router.post("/{order_id}/upload-signed", response_model=OrderResponse)
def upload_signed_requisition(
    order_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Pending Requisition -> Signed Requisition Uploaded with file upload."""
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.deleted_at == None
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if order.status != OrderStatus.PENDING_REQUISITION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition from {order.status} to signed_requisition_uploaded"
        )
    
    # Handle file upload
    try:
        content = file.file.read()
        
        # Validate file type
        if not file.filename or not file.filename.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be PDF or image (JPG, PNG)"
            )
        
        if len(content) > 1 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File too large (max 1MB)"
            )

        # For image uploads, validate 1:1 aspect ratio
        if file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            try:
                from io import BytesIO
                from PIL import Image as PILImage
                img = PILImage.open(BytesIO(content))
                w, h = img.size
                allowed_diff = int(max(w, h) * 0.02)
                if abs(w - h) > allowed_diff:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Signature image must be square (1:1 aspect ratio). Got {w}x{h}"
                    )
            except HTTPException:
                raise
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Could not validate image dimensions. Ensure the file is a valid image."
                )
        
        # Get previous requisition document (to mark as superseded)
        previous_doc = db.query(Document).filter(
            Document.order_id == order.id,
            Document.doc_category == "requisition",
            Document.version_status == "current"
        ).first()
        
        # Save signed file to storage (sanitized filename)
        safe_filename = os.path.basename(file.filename) if file.filename else f"signed_{order.id}.pdf"
        storage = get_storage_backend()
        storage_path = storage.save(
            f"orders/{order.id}/signed_requisition_{safe_filename}",
            content
        )
        
        # Create new document with versioning
        new_version = (previous_doc.version + 1) if previous_doc else 1
        
        signed_doc = Document(
            order_id=order.id,
            file_name=file.filename,
            file_type=file.filename.rsplit(".", 1)[1].lower() if "." in file.filename else "pdf",
            storage_path=storage_path,
            doc_category="signed_requisition",
            version=new_version,
            version_status="current",
            parent_document_id=previous_doc.id if previous_doc else None,
            notes="Signed requisition uploaded by user",
            uploaded_by=current_user.id
        )
        db.add(signed_doc)
        
        # Mark previous document as superseded
        if previous_doc:
            previous_doc.version_status = "superseded"
        
        db.flush()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File upload failed: {str(e)}"
        )
    
    order.status = OrderStatus.SIGNED_REQUISITION_UPLOADED
    add_timeline_entry(db, order, "signed_uploaded", current_user)
    log_audit(db, user_id=current_user.id, action="order.signed_uploaded", entity_type="order", entity_id=order.id)
    db.commit()
    db.refresh(order)
    return order
@router.get("/{order_id}/download-pdf")
def download_order_pdf(
    order_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download order as a requisition PDF. Includes approver signature when available."""
    import os as _os
    from fastapi.responses import FileResponse as FastFileResponse
    import tempfile

    order = db.query(Order).options(
        selectinload(Order.items).selectinload(OrderItem.item),
        joinedload(Order.vendor),
    ).filter(
        Order.id == order_id,
        Order.deleted_at == None
    ).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    tmp_paths = []

    # Prefer to return the stored signed requisition PDF if it exists
    signed_doc = db.query(Document).filter(
        Document.order_id == order.id,
        Document.doc_category == "signed_requisition",
        Document.version_status == "current"
    ).order_by(Document.version.desc()).first()

    if signed_doc:
        try:
            storage = get_storage_backend()
            pdf_data = storage.read(signed_doc.storage_path)
            if pdf_data:
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
                tmp.write(pdf_data)
                tmp.close()
                tmp_paths.append(tmp.name)
                for p in tmp_paths:
                    background_tasks.add_task(_os.unlink, p)
                return FastFileResponse(
                    path=tmp.name,
                    media_type="application/pdf",
                    filename=f"{order.order_number}_requisition.pdf"
                )
        except Exception as e:
            logger.warning("Could not load existing PDF for order %s, regenerating: %s", order_id, str(e))

    items = [
        {
            "name": oi.item.name if oi.item else f"Item #{oi.item_id}",
            "sku": oi.item.sku if oi.item else "",
            "quantity": str(oi.quantity_ordered),
            "description": oi.item.description if oi.item else "",
        }
        for oi in order.items
    ]

    settings = db.query(Settings).first()

    creator = db.query(User).filter(User.id == order.created_by).first()

    # Look up approver signature from timeline + UserSignature
    approver_name = None
    approver_signature_base64 = None
    if order.status in ("approved", "dispatched", "delivered", "closed"):
        approval_entry = db.query(OrderTimeline).filter(
            OrderTimeline.order_id == order.id,
            OrderTimeline.action == "approved"
        ).order_by(OrderTimeline.id.desc()).first()
        if approval_entry:
            approver = db.query(User).options(
                selectinload(User.signature)
            ).filter(User.id == approval_entry.user_id).first()
            if approver:
                approver_name = approver.full_name or approver.email
                if approver.signature and approver.signature.signature_data:
                    approver_signature_base64 = approver.signature.signature_data

    pdf_gen = PDFGenerator(
        company_name=settings.company_name if settings else "Cloud9",
        logo_url=settings.company_logo_url if settings else None
    )

    pdf_bytes = pdf_gen.generate_requisition(
        order_number=order.order_number,
        vendor_name=order.vendor.name if order.vendor else "Unknown",
        vendor_address=order.vendor.address if order.vendor else "",
        items=items,
        remarks=order.remarks or "",
        delivery_address=order.delivery_address or "",
        requested_by=creator.full_name if creator else "Unknown",
        company_address=settings.company_address if settings else "",
        order_url=f"/orders/{order.id}",
        header_text=settings.pdf_header_text if settings else "",
        footer_text=settings.pdf_footer_text if settings else "",
        approver_name=approver_name,
        approver_signature_base64=approver_signature_base64,
    )

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp.write(pdf_bytes)
    tmp.close()
    tmp_paths.append(tmp.name)

    for p in tmp_paths:
        background_tasks.add_task(_os.unlink, p)

    return FastFileResponse(
        path=tmp.name,
        media_type="application/pdf",
        filename=f"{order.order_number}_requisition.pdf"
    )
@router.get("/{order_id}/download-challan")
def download_delivery_challan(
    order_id: int,
    include_signature: bool = Query(True),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download delivery challan PDF for dispatched/delivered/closed orders."""
    import os as _os
    from fastapi.responses import FileResponse as FastFileResponse
    import tempfile
    
    order = db.query(Order).options(
        selectinload(Order.items).selectinload(OrderItem.item),
        joinedload(Order.vendor),
    ).filter(
        Order.id == order_id,
        Order.deleted_at == None
    ).first()
    
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    
    # Allow challan download for dispatched, delivered, or closed orders
    if order.status not in ("dispatched", "delivered", "closed"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot generate challan for order in {order.status} status"
        )
    
    tmp_paths = []
    
    # Check for existing delivery challan document
    challan_doc = db.query(Document).filter(
        Document.order_id == order.id,
        Document.doc_category == "delivery_challan",
        Document.version_status == "current"
    ).order_by(Document.version.desc()).first()
    
    if challan_doc:
        try:
            storage = get_storage_backend()
            pdf_data = storage.read(challan_doc.storage_path)
            if pdf_data:
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
                tmp.write(pdf_data)
                tmp.close()
                tmp_paths.append(tmp.name)
                if background_tasks:
                    for p in tmp_paths:
                        background_tasks.add_task(_os.unlink, p)
                return FastFileResponse(
                    path=tmp.name,
                    media_type="application/pdf",
                    filename=f"{order.order_number}_delivery_challan.pdf"
                )
        except Exception as e:
            logger.warning("Could not load existing challan PDF for order %s, regenerating: %s", order_id, str(e))
    
    # Generate challan PDF
    items = [
        {
            "name": oi.item.name if oi.item else f"Item #{oi.item_id}",
            "sku": oi.item.sku if oi.item else "",
            "quantity_dispatched": str(oi.quantity_dispatched),
            "description": oi.item.description if oi.item else "",
        }
        for oi in order.items
    ]
    
    settings = db.query(Settings).first()
    creator = db.query(User).filter(User.id == order.created_by).first()
    
    # Get dispatcher signature if available and requested
    dispatcher_name = None
    dispatcher_signature_base64 = None
    if include_signature:
        # Get user who dispatched the order
        dispatch_entry = db.query(OrderTimeline).filter(
            OrderTimeline.order_id == order.id,
            OrderTimeline.action == "dispatched"
        ).order_by(OrderTimeline.id.desc()).first()
        
        if dispatch_entry:
            dispatcher = db.query(User).options(
                selectinload(User.signature)
            ).filter(User.id == dispatch_entry.user_id).first()
            if dispatcher:
                dispatcher_name = dispatcher.full_name or dispatcher.email
                if dispatcher.signature and dispatcher.signature.signature_data:
                    dispatcher_signature_base64 = dispatcher.signature.signature_data
    
    # Get challan book number from existing document if available
    challan_book_number = challan_doc.challan_book_number if challan_doc else ""
    
    pdf_gen = PDFGenerator(
        company_name=settings.company_name if settings else "Cloud9",
        logo_url=settings.company_logo_url if settings else None
    )
    
    pdf_bytes = pdf_gen.generate_delivery_challan(
        order_number=order.order_number,
        vendor_name=order.vendor.name if order.vendor else "Unknown",
        items=items,
        challan_book_number=challan_book_number,
        requested_by=creator.full_name if creator else "Unknown",
        company_address=settings.company_address if settings else "",
        header_text=settings.pdf_header_text if settings else "",
        footer_text=settings.pdf_footer_text if settings else "",
        dispatch_signature_base64=dispatcher_signature_base64,
    )
    
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp.write(pdf_bytes)
    tmp.close()
    tmp_paths.append(tmp.name)
    
    if background_tasks:
        for p in tmp_paths:
            background_tasks.add_task(_os.unlink, p)
    
    return FastFileResponse(
        path=tmp.name,
        media_type="application/pdf",
        filename=f"{order.order_number}_delivery_challan.pdf"
    )
