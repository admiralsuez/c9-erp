from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.core.database import get_db
from app.core.auth import get_current_user, require_admin
from app.models import User, Vendor, VendorType
from app.schemas import VendorCreate, VendorUpdate, VendorResponse, VendorSummaryResponse, VendorTypeResponse, VendorTypeCreate
from app.schemas.imports import VendorImportRow, ImportResult, ImportError, get_vendor_template
from app.services.csv_importer import parse_csv_file, validate_and_parse_rows, validate_headers, get_required_headers
from typing import List
from difflib import SequenceMatcher
from datetime import datetime, timezone

router = APIRouter(prefix="/vendors", tags=["Vendors"])


def normalize_vendor_name(name: str) -> str:
    """Normalize vendor name for dedup check."""
    return name.strip().lower()


def find_similar_vendors(name: str, db: Session, exclude_id: int = None) -> List[Vendor]:
    """Find vendors with exact name match only (no fuzzy matching to avoid false 409s).
    Only block truly identical/normalized names, not similar ones.
    """
    normalized = normalize_vendor_name(name)
    
    # Only check for exact normalized match
    existing = db.query(Vendor).filter(
        Vendor.deleted_at == None,
        Vendor.name_normalized == normalized
    ).all()
    
    similar = []
    for vendor in existing:
        if exclude_id and vendor.id == exclude_id:
            continue
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
    query = db.query(Vendor).filter(
        Vendor.deleted_at == None,
        Vendor.parent_id == None  # Child addresses not listed as standalone vendors
    )
    
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
    
    # Child addresses (parent_id set) skip vendor-name dedup checks
    if vendor_data.parent_id is None:
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
        vendor_type_id=vendor_data.vendor_type_id,
        contact_person=vendor_data.contact_person,
        phone=vendor_data.phone,
        email=vendor_data.email,
        address=vendor_data.address,
        city=vendor_data.city,
        state=vendor_data.state,
        pincode=vendor_data.pincode,
        gst=vendor_data.gst,
        notes=vendor_data.notes,
        parent_id=vendor_data.parent_id
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


# ============ VENDOR TYPES ============
@router.get("/types", response_model=List[VendorTypeResponse])
def list_vendor_types(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(VendorType).order_by(VendorType.name).all()


@router.post("/types", response_model=VendorTypeResponse, status_code=status.HTTP_201_CREATED)
def create_vendor_type(body: VendorTypeCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    existing = db.query(VendorType).filter(VendorType.name == body.name).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Vendor type already exists")
    vt = VendorType(name=body.name)
    db.add(vt)
    db.commit()
    db.refresh(vt)
    return vt


@router.delete("/types/{type_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vendor_type(type_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    vt = db.query(VendorType).filter(VendorType.id == type_id).first()
    if not vt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor type not found")
    vendors_using = db.query(Vendor).filter(Vendor.vendor_type_id == type_id).count()
    if vendors_using > 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Cannot delete: {vendors_using} vendor(s) use this type")
    db.delete(vt)
    db.commit()


# ============ BULK IMPORT ============
@router.get("/import/template")
def get_vendor_import_template():
    """Get CSV template for vendor import"""
    return get_vendor_template()


@router.post("/import", response_model=ImportResult)
def import_vendors(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("vendors.create"))
):
    """Bulk import vendors from CSV file.
    
    CSV must have columns: name, vendor_type_id, contact_person, phone, email, address, city, state, gst
    
    Returns detailed import results with errors by row number.
    """
    try:
        # Read file
        contents = file.file.read()
        if not contents:
            raise ValueError('File is empty')
        
        # Parse CSV
        headers, rows = parse_csv_file(contents)
        
        # Validate headers
        required_headers = ['name']
        is_valid, error_msg = validate_headers(headers, required_headers)
        if not is_valid:
            raise ValueError(error_msg)
        
        # Validate and parse rows
        valid_rows, validation_errors = validate_and_parse_rows(rows, VendorImportRow)
        
        # Check for duplicates and FK issues
        all_errors = list(validation_errors)
        created_count = 0
        
        # Create valid vendors in a transaction
        try:
            for vendor_data in valid_rows:
                normalized_name = normalize_vendor_name(vendor_data.name)
                
                # Check for existing vendor with same normalized name
                existing = db.query(Vendor).filter(
                    Vendor.name_normalized == normalized_name,
                    Vendor.deleted_at == None
                ).first()
                
                if existing:
                    all_errors.append(ImportError(
                        row_number=len(all_errors) + 2,
                        reason=f"Duplicate vendor name: '{vendor_data.name}'",
                        values=vendor_data.model_dump()
                    ))
                    continue
                
                # Check vendor_type_id if provided
                if vendor_data.vendor_type_id:
                    vtype = db.query(VendorType).filter(VendorType.id == vendor_data.vendor_type_id).first()
                    if not vtype:
                        all_errors.append(ImportError(
                            row_number=len(all_errors) + 2,
                            reason=f"Vendor type ID {vendor_data.vendor_type_id} not found",
                            values=vendor_data.model_dump()
                        ))
                        continue
                
                # Create vendor
                vendor = Vendor(
                    name=vendor_data.name,
                    name_normalized=normalized_name,
                    vendor_type_id=vendor_data.vendor_type_id,
                    contact_person=vendor_data.contact_person,
                    phone=vendor_data.phone,
                    email=vendor_data.email,
                    address=vendor_data.address,
                    city=vendor_data.city,
                    state=vendor_data.state,
                    pincode=vendor_data.pincode,
                    gst=vendor_data.gst,
                    notes=vendor_data.notes,
                )
                db.add(vendor)
                created_count += 1
            
            db.commit()
        except Exception as e:
            db.rollback()
            raise ValueError(f"Database error: {str(e)}")
        
        return ImportResult(
            success=len(all_errors) == 0,
            total_rows=len(rows),
            successful=created_count,
            failed=len(all_errors),
            errors=all_errors,
            message=f"Imported {created_count} vendors successfully. {len(all_errors)} rows had errors."
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {str(e)}"
        )
