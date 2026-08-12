"""Vendor portal security helpers: rate limiting, token hashing, session auth."""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models import Vendor
from typing import Optional
from datetime import datetime, timezone, timedelta
import hashlib
import time as _time
import secrets

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
