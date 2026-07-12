from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_user, require_admin
from app.models import User, Document, Order
from app.schemas import DocumentResponse, DocumentVersionHistoryResponse
from app.services.storage import get_storage_backend, LocalDiskBackend
from typing import List, Optional
from datetime import datetime, timezone
import os
import mimetypes

router = APIRouter(prefix="/documents", tags=["Documents"])

# Allowed file types
ALLOWED_FILE_TYPES = {"pdf", "jpg", "jpeg", "png", "docx", "xlsx"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


def get_file_type(filename: str) -> str:
    """Extract file type from filename."""
    if "." not in filename:
        return ""
    return filename.rsplit(".", 1)[1].lower()


def validate_file(filename: str, file_size: int) -> tuple:
    """Validate file before upload."""
    file_type = get_file_type(filename)
    
    if file_type not in ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type .{file_type} not allowed. Allowed: {', '.join(ALLOWED_FILE_TYPES)}"
        )
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024}MB"
        )
    
    return file_type


@router.post("/upload/{order_id}", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    order_id: int,
    doc_category: str = Query(...),
    notes: Optional[str] = None,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a document to an order.
    
    Args:
        order_id: Order ID
        doc_category: Document category (requisition, signed_requisition, etc.)
        notes: Optional notes
        file: File to upload
        
    Returns:
        Document metadata
    """
    # Verify order exists
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Read file content
    content = await file.read()
    file_type = validate_file(file.filename, len(content))
    
    # Save file using storage backend (sanitized filename)
    safe_filename = os.path.basename(file.filename) if file.filename else f"document_{order_id}"
    storage = get_storage_backend()
    storage_path = storage.save(
        f"orders/{order_id}/{safe_filename}",
        content
    )
    
    # Create document record
    document = Document(
        order_id=order_id,
        file_name=file.filename,
        file_type=file_type,
        storage_path=storage_path,
        doc_category=doc_category,
        version=1,
        version_status="current",
        notes=notes,
        uploaded_by=current_user.id
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    return document


@router.get("/orders/{order_id}/documents")
def list_order_documents(
    order_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all documents for an order (current versions only)."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    query = db.query(Document).filter(
        Document.order_id == order_id,
        Document.version_status == "current"
    )
    total = query.count()
    skip = (page - 1) * size
    documents = query.offset(skip).limit(size).all()
    
    return {
        "items": [DocumentResponse.model_validate(d) for d in documents],
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size if total > 0 else 1
    }


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get document metadata."""
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return document


@router.get("/{document_id}/download")
def download_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download/view a document file."""
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    storage = get_storage_backend()
    
    # Local disk backend: serve directly from disk with FileResponse
    if isinstance(storage, LocalDiskBackend):
        full_path = os.path.normpath(
            os.path.join(storage.base_path, document.storage_path)
        )
        # Prevent path traversal: ensure the resolved path is within base_path
        if not full_path.startswith(os.path.normpath(storage.base_path) + os.sep):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file path"
            )
        if not os.path.exists(full_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found on disk"
            )
        media_type, _ = mimetypes.guess_type(document.file_name)
        return FileResponse(
            path=full_path,
            media_type=media_type or "application/octet-stream",
            filename=document.file_name
        )
    
    # S3 or other backend: return signed URL or raw bytes
    file_content = storage.read(document.storage_path)
    if file_content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found in storage"
        )
    media_type, _ = mimetypes.guess_type(document.file_name)
    from fastapi.responses import Response
    return Response(
        content=file_content,
        media_type=media_type or "application/octet-stream",
        headers={"Content-Disposition": f'inline; filename="{document.file_name}"'}
    )


@router.get("/{document_id}/versions", response_model=List[DocumentVersionHistoryResponse])
def get_document_versions(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get version history for a document."""
    # Get the current document
    current_doc = db.query(Document).filter(Document.id == document_id).first()
    
    if not current_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Get all versions in the chain
    versions = []
    doc = current_doc
    
    while doc:
        versions.append(doc)
        # Find parent document
        if doc.parent_document_id:
            doc = db.query(Document).filter(Document.id == doc.parent_document_id).first()
        else:
            break
    
    return versions


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def soft_delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Soft delete a document (mark as archived)."""
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Update version_status to archived (soft delete)
    document.version_status = "archived"
    db.commit()
