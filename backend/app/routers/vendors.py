from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.core.database import get_db
from app.core.auth import get_current_user, require_admin
from app.models import User, Vendor
from app.schemas import VendorCreate, VendorUpdate, VendorResponse, VendorSummaryResponse
from typing import List
from difflib import SequenceMatcher
from datetime import datetime, timezone

router = APIRouter(prefix="/vendors", tags=["Vendors"])


def normalize_vendor_name(name: str) -> str:
    """Normalize vendor name for dedup check."""
    return name.strip().lower()


def find_similar_vendors(name: str, db: Session, exclude_id: int = None) -> List[Vendor]:
    """Find vendors with similar names using fuzzy matching.
    Uses DB-level filtering first to reduce the set, then fuzzy matches in Python.
    """
    normalized = normalize_vendor_name(name)
    threshold = 0.6  # 60% similarity
    
    # First pass: DB-level filter to reduce candidates (ILIKE prefix + exact normal)
    prefix = normalized[:3] if len(normalized) >= 3 else normalized
    candidates = db.query(Vendor).filter(
        Vendor.deleted_at == None,
        or_(
            Vendor.name_normalized == normalized,
            Vendor.name_normalized.ilike(f"{prefix}%")
        )
    ).all()
    
    # Second pass: fuzzy matching on reduced set
    similar = []
    for vendor in candidates:
        if exclude_id and vendor.id == exclude_id:
            continue
        if vendor.name_normalized == normalized:
            similar.append(vendor)
        else:
            ratio = SequenceMatcher(None, normalized, vendor.name_normalized).ratio()
            if ratio >= threshold:
                similar.append(vendor)
    
    return similar


@router.get("")
def list_vendors(
    search: str = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List vendors with optional search - returns paginated response."""
    query = db.query(Vendor).filter(Vendor.deleted_at == None)
    
    if search:
        normalized_search = normalize_vendor_name(search)
        query = query.filter(
            or_(
                Vendor.name_normalized.ilike(f"%{normalized_search}%"),
                Vendor.name.ilike(f"%{search}%"),
                Vendor.email.ilike(f"%{search}%"),
                Vendor.phone.ilike(f"%{search}%")
            )
        )
    
    total = query.count()
    skip = (page - 1) * size
    vendors = query.offset(skip).limit(size).all()
    pages = (total + size - 1) // size if total > 0 else 1
    
    return {
        "items": [VendorResponse.model_validate(v) for v in vendors],
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }


@router.post("", response_model=VendorResponse, status_code=status.HTTP_201_CREATED)
def create_vendor(
    vendor_data: VendorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new vendor with duplicate detection."""
    normalized_name = normalize_vendor_name(vendor_data.name)
    
    # Check for exact match
    existing = db.query(Vendor).filter(
        Vendor.name_normalized == normalized_name,
        Vendor.deleted_at == None
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Vendor with similar name already exists: {existing.name}"
        )
    
    # Check for fuzzy matches and block with 409
    similar = find_similar_vendors(vendor_data.name, db)
    if similar:
        similar_names = [v.name for v in similar]
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Similar vendor already exists: {', '.join(similar_names)}"
        )
    
    vendor = Vendor(
        name=vendor_data.name,
        name_normalized=normalized_name,
        vendor_type=vendor_data.vendor_type,
        contact_person=vendor_data.contact_person,
        phone=vendor_data.phone,
        email=vendor_data.email,
        address=vendor_data.address,
        city=vendor_data.city,
        state=vendor_data.state,
        gst=vendor_data.gst,
        notes=vendor_data.notes
    )
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    return vendor


@router.get("/{vendor_id}", response_model=VendorResponse)
def get_vendor(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get vendor by ID."""
    vendor = db.query(Vendor).filter(
        Vendor.id == vendor_id,
        Vendor.deleted_at == None
    ).first()
    
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    return vendor


@router.patch("/{vendor_id}", response_model=VendorResponse)
def update_vendor(
    vendor_id: int,
    vendor_data: VendorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update vendor."""
    vendor = db.query(Vendor).filter(
        Vendor.id == vendor_id,
        Vendor.deleted_at == None
    ).first()
    
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    # If name is being updated, check for duplicates
    if vendor_data.name:
        normalized_name = normalize_vendor_name(vendor_data.name)
        existing = db.query(Vendor).filter(
            Vendor.name_normalized == normalized_name,
            Vendor.id != vendor_id,
            Vendor.deleted_at == None
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Vendor with similar name already exists: {existing.name}"
            )
        
        vendor.name = vendor_data.name
        vendor.name_normalized = normalized_name
    
    # Update other fields
    update_data = vendor_data.model_dump(exclude_unset=True, exclude={"name"})
    for field, value in update_data.items():
        if value is not None:
            setattr(vendor, field, value)
    
    db.commit()
    db.refresh(vendor)
    return vendor


@router.delete("/{vendor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vendor(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Soft delete vendor."""
    vendor = db.query(Vendor).filter(
        Vendor.id == vendor_id,
        Vendor.deleted_at == None
    ).first()
    
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    vendor.deleted_at = datetime.now(timezone.utc)
    db.commit()


@router.post("/{vendor_id}/restore", response_model=VendorResponse)
def restore_vendor(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Restore soft-deleted vendor."""
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    if not vendor.deleted_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vendor is not deleted"
        )
    
    vendor.deleted_at = None
    db.commit()
    db.refresh(vendor)
    return vendor


@router.get("/{vendor_id}/summary", response_model=VendorSummaryResponse)
def get_vendor_summary(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get vendor summary with order stats (placeholder for Phase 2)."""
    vendor = db.query(Vendor).filter(
        Vendor.id == vendor_id,
        Vendor.deleted_at == None
    ).first()
    
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    # In Phase 2, this will include order statistics
    return VendorSummaryResponse(
        id=vendor.id,
        name=vendor.name,
        vendor_type=vendor.vendor_type,
        contact_person=vendor.contact_person,
        phone=vendor.phone,
        email=vendor.email,
        address=vendor.address,
        city=vendor.city,
        state=vendor.state,
        gst=vendor.gst,
        notes=vendor.notes,
        is_active=vendor.is_active,
        created_at=vendor.created_at,
        updated_at=vendor.updated_at,
        total_orders=0,
        total_quantity_ordered=0
    )
