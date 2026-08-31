from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import or_, asc, desc, func
from app.core.database import get_db
from app.core.auth import get_current_user, require_admin, require_permission
from app.models import User, Vendor, VendorType
from app.schemas import VendorCreate, VendorUpdate, VendorResponse, VendorSummaryResponse, VendorTypeResponse, VendorTypeCreate
from app.schemas.imports import VendorImportRow, ImportResult, get_vendor_template
from app.services.csv_importer import parse_csv_file, validate_and_parse_rows, validate_headers, get_required_headers
from typing import List, Optional
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
    vendor_type: str = Query(None),
    city: str = Query(None),
    sort_by: str = Query(None, pattern="^(last_added|old_to_new|by_city)$"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List vendors with search, type/city filter, and sorting - returns paginated response."""
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
    
    if vendor_type:
        query = query.filter(Vendor.vendor_type == vendor_type)
    
    if city:
        query = query.filter(Vendor.city.ilike(f"%{city}%"))
    
    # Apply sorting
    if sort_by == "last_added":
        query = query.order_by(desc(Vendor.created_at))
    elif sort_by == "old_to_new":
        query = query.order_by(asc(Vendor.created_at))
    elif sort_by == "by_city":
        query = query.order_by(asc(Vendor.city))
    
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
    
    # Resolve legacy vendor_type string from the FK when not provided
    vendor_type_str = vendor_data.vendor_type
    if not vendor_type_str and vendor_data.vendor_type_id:
        vt = db.query(VendorType).filter(VendorType.id == vendor_data.vendor_type_id).first()
        if vt:
            vendor_type_str = vt.name

    vendor = Vendor(
        name=vendor_data.name,
        name_normalized=normalized_name,
        vendor_type=vendor_type_str,
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


@router.get("/types/{type_id}/vendors-using")
def get_vendors_using_type(type_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get vendors using a specific vendor type."""
    vt = db.query(VendorType).filter(VendorType.id == type_id).first()
    if not vt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor type not found")
    
    vendors = db.query(Vendor).filter(
        Vendor.vendor_type_id == type_id,
        Vendor.deleted_at == None
    ).all()
    
    return {
        "vendor_type": vt,
        "vendors": [VendorResponse.model_validate(v) for v in vendors],
        "count": len(vendors)
    }


@router.post("/types/{type_id}/reassign-and-delete")
def reassign_vendors_and_delete_type(
    type_id: int,
    new_type_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reassign all vendors to a new type and delete the old type."""
    vt = db.query(VendorType).filter(VendorType.id == type_id).first()
    if not vt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor type not found")
    
    # Include soft-deleted vendors too — they still hold the FK and would
    # block deletion with a constraint violation if left pointing at this type
    active_vendors = db.query(Vendor).filter(
        Vendor.vendor_type_id == type_id,
        Vendor.deleted_at == None
    ).all()
    all_vendors = db.query(Vendor).filter(
        Vendor.vendor_type_id == type_id
    ).all()

    if len(all_vendors) == 0:
        # No vendors using this type at all, just delete it
        db.delete(vt)
        db.commit()
        return {"message": "Vendor type deleted successfully"}

    if new_type_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete: {len(active_vendors)} active vendor(s) use this type. Provide new_type_id to reassign them."
        )

    # Verify new type exists
    new_type = db.query(VendorType).filter(VendorType.id == new_type_id).first()
    if not new_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="New vendor type not found")

    # Reassign ALL vendors (including soft-deleted) so the FK is released.
    # Also update the legacy vendor_type string so the UI stays consistent.
    for vendor in all_vendors:
        vendor.vendor_type_id = new_type_id
        vendor.vendor_type = new_type.name

    # Delete old type
    db.delete(vt)
    db.commit()
    
    return {
        "message": f"Reassigned {len(active_vendors)} vendor(s) to {new_type.name} and deleted {vt.name}",
        "reassigned_count": len(active_vendors),
        "new_type": VendorTypeResponse.model_validate(new_type)
    }


@router.delete("/types/{type_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vendor_type(type_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    vt = db.query(VendorType).filter(VendorType.id == type_id).first()
    if not vt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor type not found")
    # Only active vendors block deletion
    vendors_using = db.query(Vendor).filter(
        Vendor.vendor_type_id == type_id,
        Vendor.deleted_at == None
    ).count()
    if vendors_using > 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Cannot delete: {vendors_using} vendor(s) use this type")
    # Clear FK on soft-deleted vendors so the delete doesn't violate the constraint
    db.query(Vendor).filter(
        Vendor.vendor_type_id == type_id
    ).update({"vendor_type_id": None, "vendor_type": None}, synchronize_session=False)
    db.delete(vt)
    db.commit()


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

    # Keep legacy vendor_type string in sync with the FK
    if vendor_data.vendor_type_id is not None:
        vt = db.query(VendorType).filter(VendorType.id == vendor_data.vendor_type_id).first()
        if vt:
            vendor.vendor_type = vt.name

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
