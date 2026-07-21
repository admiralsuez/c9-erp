from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from app.core.database import get_db
from app.core.auth import (
    hash_password, verify_password, create_access_token,
    create_refresh_token, verify_token, get_current_user
)
from app.models import User, RefreshToken
from app.services.audit_service import log_audit
from app.schemas import LoginRequest, TokenResponse, RefreshTokenRequest, UserResponse
from collections import defaultdict
import hashlib
import time
import logging

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = logging.getLogger(__name__)

# Simple in-memory rate limiter (per IP)
_login_attempts: dict = defaultdict(list)
LOGIN_RATE_LIMIT = 10  # max attempts
LOGIN_RATE_WINDOW = 300  # seconds (5 min)


def _check_login_rate_limit(ip: str):
    now = time.time()
    window_start = now - LOGIN_RATE_WINDOW
    _login_attempts[ip] = [t for t in _login_attempts[ip] if t > window_start]
    if len(_login_attempts[ip]) >= LOGIN_RATE_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many login attempts. Try again in {LOGIN_RATE_WINDOW // 60} minutes."
        )
    _login_attempts[ip].append(now)


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, http_request: Request, db: Session = Depends(get_db)):
    """Login with email and password, return access + refresh tokens."""
    # print("reached herrrrrrrrrrrrrrrrrrrrrrrrrrrrrr")
    ip = http_request.client.host if http_request.client else "unknown"
    _check_login_rate_limit(ip)
    
    user = db.query(User).filter(
        User.email == request.email,
        User.is_active == True,
        User.deleted_at == None
    ).first()
    
    if not user or not verify_password(request.password, user.password_hash):
        logger.warning("LOGIN FAIL %s from %s", request.email, ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    logger.info("LOGIN OK %s (%s) from %s", request.email, user.full_name, ip)
    
    # Upgrade legacy SHA-256 hashes to bcrypt on successful login
    if not user.password_hash.startswith(('$2b$', '$2a$', '$2y$')):
        user.password_hash = hash_password(request.password)
        db.commit()
    
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id, db)
    
    log_audit(db, user_id=user.id, action="login", entity_type="user", entity_id=user.id, ip_address=ip)

    # Import UserResponse schema for serialization
    user_data = UserResponse.model_validate(user)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user_data
    }


@router.post("/refresh", response_model=TokenResponse)
def refresh(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Refresh an access token using a refresh token."""
    try:
        payload = verify_token(request.refresh_token)
        user_id = payload.get("user_id")
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Verify refresh token exists, is not revoked, and not expired
    token_hash = hashlib.sha256(request.refresh_token.encode()).hexdigest()
    refresh_token_record = db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.token_hash == token_hash
    ).first()
    
    if not refresh_token_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found"
        )
    
    if refresh_token_record.revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked"
        )
    
    if refresh_token_record.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired"
        )
    
    # Verify user still exists and is active
    user = db.query(User).filter(
        User.id == user_id,
        User.is_active == True,
        User.deleted_at == None
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Rotate refresh token: revoke old, issue new
    refresh_token_record.revoked = True
    new_refresh_token = create_refresh_token(user_id, db)
    
    access_token = create_access_token(user_id)
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user info. Used for session restoration on page reload."""
    return current_user


@router.post("/change-password")
def change_password(
    old_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change password for the authenticated user."""
    if not verify_password(old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters"
        )
    
    current_user.password_hash = hash_password(new_password)
    db.commit()
    
    return {"message": "Password changed successfully"}


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Logout - revoke all refresh tokens for the current user."""
    # Mark all refresh tokens for this user as revoked
    db.query(RefreshToken).filter(
        RefreshToken.user_id == current_user.id,
        RefreshToken.revoked == False
    ).update({RefreshToken.revoked: True})
    db.commit()
    
    return {"message": "Logged out successfully"}
