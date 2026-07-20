from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Header
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.models import Vendor, Order, Document
from app.schemas import OrderResponse
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import secrets
import hashlib
import time as _time
from app.services.storage import get_storage_backend
from jose import jwt as jose_jwt, JWTError

router = APIRouter(prefix="/vendor-portal", tags=["Vendor Portal"])

# Simple in-memory rate limiter for vendor login (5 attempts per minute per IP)
_login_attempts = {}
def _check_login_rate_limit(ip: str):
    now = _time.time()
    window = 60
    for key in list(_login_attempts.keys()):
        if now - _login_attempts[key][0] > window * 2:
            del _login_attempts[key]
    if ip not in _login_attempts:
        _login_attempts[ip] = (now, 1)
        return
    ts, count = _login_attempts[ip]
    if now - ts > window:
        _login_attempts[ip] = (now, 1)
        return
    if count >= 5:
        raise HTTPException(status_code=429, detail="Too many login attempts. Try again later.")
    _login_attempts[ip] = (ts, count + 1)


def hash_vendor_token(token: str) -> str:
    """SHA-256 hash of vendor token for storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def get_vendor_from_token(authorization: str, db: Session) -> Vendor:
    """
    Validate vendor session token from Authorization header.
    Returns vendor. Raises HTTPException if invalid.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")

    token_hash = hash_vendor_token(token)
    vendor = db.query(Vendor).filter(
        Vendor.vendor_token_hash == token_hash,
        Vendor.allow_portal == True,
        Vendor.deleted_at == None
    ).first()
    
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired vendor token"
        )
    
    expires = vendor.vendor_token_expires_at
    if expires:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        expires_naive = expires.replace(tzinfo=None) if expires.tzinfo else expires
        if expires_naive < now:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Vendor token expired"
            )
    
    return vendor


def refresh_vendor_token(vendor: Vendor, db: Session):
    """Refresh vendor token expiry (90 days from now)."""
    vendor.vendor_token_expires_at = datetime.now(timezone.utc) + timedelta(days=90)
    db.commit()


def _generate_session_token() -> str:
    """Generate a unique session token."""
    return secrets.token_urlsafe(24)


@router.post("/request-magic-link")
def request_magic_link(
    email: str = Query(...),
    request: Request = None,
    db: Session = Depends(get_db),
):
    """
    Request a magic link sent to the vendor's email.
    The magic link is only sent via email (never returned in the response).
    Responds with a generic message regardless of whether the vendor exists.
    """
    ip = request.client.host if request and request.client else "unknown"
    _check_login_rate_limit(ip)

    vendor = db.query(Vendor).filter(
        Vendor.email == email,
        Vendor.allow_portal == True,
        Vendor.deleted_at == None
    ).first()
    
    if not vendor:
        # Return generic message to prevent email enumeration
        return {
            "message": "If a vendor with this email exists, a magic link has been sent.",
        }

    # Generate short-lived JWT (15 min)
    magic_link_jwt = jose_jwt.encode(
        {
            "sub": f"vendor:{vendor.id}",
            "email": vendor.email,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
            "iat": datetime.now(timezone.utc),
            "type": "vendor_magic_link",
        },
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )

    # Try to email the magic link; fail silently if email not configured
    magic_url = f"{request.base_url}vendor-portal/verify-magic-link?token={magic_link_jwt}"
    email_sent = False
    try:
        from app.services.email_service import get_email_service
        svc = get_email_service()
        svc.send_email(
            to_email=vendor.email,
            subject="Your Cloud9 ERP Portal Login Link",
            body_html=f"""<h2>Cloud9 ERP Vendor Portal</h2>
<p>Click the link below to log in to your vendor portal:</p>
<p><a href="{magic_url}">Log in to Portal</a></p>
<p>This link expires in 15 minutes.</p>
<p>If you did not request this, please ignore this email.</p>""",
        )
        email_sent = True
    except Exception:
        pass

    return {
        "message": "If a vendor with this email exists, a magic link has been sent.",
    }


@router.get("/verify-magic-link")
def verify_magic_link(
    token: str = Query(..., description="JWT from magic link email"),
    db: Session = Depends(get_db),
):
    """Verify a magic-link JWT and return a session token."""
    try:
        payload = jose_jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired magic link")

    if payload.get("type") != "vendor_magic_link":
        raise HTTPException(status_code=401, detail="Invalid token type")

    vendor_id = int(payload.get("sub", "").replace("vendor:", ""))
    vendor = db.query(Vendor).filter(
        Vendor.id == vendor_id,
        Vendor.allow_portal == True,
        Vendor.deleted_at == None
    ).first()

    if not vendor:
        raise HTTPException(status_code=401, detail="Vendor not found or portal disabled")

    # Generate session token (store hash, return raw)
    session_token = _generate_session_token()
    vendor.vendor_token_hash = hash_vendor_token(session_token)
    vendor.vendor_token_expires_at = datetime.now(timezone.utc) + timedelta(days=90)

    # Drop plaintext vendor_token if present
    vendor.vendor_token = None

    db.commit()

    return {
        "vendor_id": vendor.id,
        "vendor_name": vendor.name,
        "vendor_token": session_token,
        "token_type": "bearer",
        "expires_at": vendor.vendor_token_expires_at.isoformat(),
    }


@router.get("/orders")
def list_vendor_orders(
    authorization: str = Header(...),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List all orders for a vendor (read-only access).
    Returns open and recent orders.
    """
    vendor = get_vendor_from_token(authorization, db)
    refresh_vendor_token(vendor, db)
    
    query = db.query(Order).filter(
        Order.vendor_id == vendor.id,
        Order.deleted_at == None
    )
    
    if status:
        query = query.filter(Order.status == status)
    
    # Order by most recent first
    query = query.order_by(Order.created_at.desc())
    
    skip = (page - 1) * size
    orders = query.offset(skip).limit(size).all()
    
    return {
        "vendor_id": vendor.id,
        "vendor_name": vendor.name,
        "orders": orders,
        "page": page,
        "page_size": size,
        "total": query.count()
    }


@router.get("/orders/{order_id}")
def get_vendor_order(
    order_id: int,
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific order.
    Vendor can only access their own orders.
    """
    vendor = get_vendor_from_token(authorization, db)
    refresh_vendor_token(vendor, db)
    
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.vendor_id == vendor.id,
        Order.deleted_at == None
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Prepare response with order details and timeline
    return {
        "order": order,
        "timeline": order.timeline_entries,
        "items": order.items,
        "documents": db.query(Document).filter(
            Document.order_id == order_id,
            Document.version_status.in_(["current"])
        ).all()
    }


@router.get("/orders/{order_id}/download/{document_id}")
def download_order_document(
    order_id: int,
    document_id: int,
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    """
    Download a document associated with an order.
    Vendor can only download documents from their own orders.
    """
    vendor = get_vendor_from_token(authorization, db)
    refresh_vendor_token(vendor, db)
    
    # Verify order belongs to vendor
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.vendor_id == vendor.id,
        Order.deleted_at == None
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Get document
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.order_id == order_id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Read file from storage
    storage = get_storage_backend()
    file_content = storage.read(document.storage_path)
    
    if not file_content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found in storage"
        )
    
    return {
        "file_name": document.file_name,
        "file_type": document.file_type,
        "content": file_content,
        "size": len(file_content)
    }


@router.get("/dashboard")
def get_vendor_dashboard(
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    """
    Get vendor dashboard with summary statistics.
    """
    vendor = get_vendor_from_token(authorization, db)
    refresh_vendor_token(vendor, db)
    
    # Get statistics
    total_orders = db.query(Order).filter(
        Order.vendor_id == vendor.id,
        Order.deleted_at == None
    ).count()
    
    pending_orders = db.query(Order).filter(
        Order.vendor_id == vendor.id,
        Order.status.in_(["pending_requisition", "signed_requisition_uploaded"]),
        Order.deleted_at == None
    ).count()
    
    approved_orders = db.query(Order).filter(
        Order.vendor_id == vendor.id,
        Order.status == "approved",
        Order.deleted_at == None
    ).count()
    
    dispatched_orders = db.query(Order).filter(
        Order.vendor_id == vendor.id,
        Order.status == "dispatched",
        Order.deleted_at == None
    ).count()
    
    delivered_orders = db.query(Order).filter(
        Order.vendor_id == vendor.id,
        Order.status == "delivered",
        Order.deleted_at == None
    ).count()
    
    # Get recent orders
    recent_orders = db.query(Order).filter(
        Order.vendor_id == vendor.id,
        Order.deleted_at == None
    ).order_by(Order.created_at.desc()).limit(5).all()
    
    return {
        "vendor_id": vendor.id,
        "vendor_name": vendor.name,
        "contact_person": vendor.contact_person,
        "email": vendor.email,
        "statistics": {
            "total_orders": total_orders,
            "pending_orders": pending_orders,
            "approved_orders": approved_orders,
            "dispatched_orders": dispatched_orders,
            "delivered_orders": delivered_orders
        },
        "recent_orders": recent_orders
    }


@router.post("/search-orders")
def search_vendor_orders(
    authorization: str = Header(...),
    order_number: Optional[str] = None,
    status: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Search vendor orders with filters.
    """
    vendor = get_vendor_from_token(authorization, db)
    refresh_vendor_token(vendor, db)
    
    query = db.query(Order).filter(
        Order.vendor_id == vendor.id,
        Order.deleted_at == None
    )
    
    if order_number:
        query = query.filter(Order.order_number.ilike(f"%{order_number}%"))
    
    if status:
        query = query.filter(Order.status == status)
    
    if from_date:
        try:
            from_datetime = datetime.fromisoformat(from_date)
            query = query.filter(Order.created_at >= from_datetime)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid from_date format. Use ISO format (YYYY-MM-DD)"
            )
    
    if to_date:
        try:
            to_datetime = datetime.fromisoformat(to_date)
            query = query.filter(Order.created_at <= to_datetime)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid to_date format. Use ISO format (YYYY-MM-DD)"
            )
    
    orders = query.order_by(Order.created_at.desc()).all()
    
    return {
        "vendor_id": vendor.id,
        "vendor_name": vendor.name,
        "search_results": orders,
        "count": len(orders)
    }
