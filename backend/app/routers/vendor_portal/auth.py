"""Vendor portal authentication: magic link login flow."""

from fastapi import APIRouter, Query, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.models import Vendor
from datetime import datetime, timezone, timedelta
from jose import jwt as jose_jwt, JWTError

from app.routers.vendor_portal.security import _check_login_rate_limit, hash_vendor_token, _generate_session_token

router = APIRouter(prefix="/vendor-portal", tags=["Vendor Portal"])

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
        from app.services.email_service import safe_send_templated_email
        email_sent = safe_send_templated_email(
            to_email=vendor.email,
            template={"subject": "Your Cloud9 ERP Portal Login Link",
                      "body_html": f"""<h2>Cloud9 ERP Vendor Portal</h2>
<p>Click the link below to log in to your vendor portal:</p>
<p><a href="{magic_url}">Log in to Portal</a></p>
<p>This link expires in 15 minutes.</p>
<p>If you did not request this, please ignore this email.</p>"""},
            context={},
            context_label="vendor-portal-magic-link",
        )
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
