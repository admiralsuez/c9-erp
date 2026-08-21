from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from app.core.database import get_db
from app.core.auth import (
    hash_password, verify_password, create_access_token,
    create_refresh_token, verify_token, get_current_user,
    create_password_reset_token, verify_password_reset_token, mark_password_reset_token_used
)
from app.models import User, RefreshToken
from app.schemas import PasswordResetRequest, PasswordResetConfirm, PasswordResetResponse
from app.services.audit_service import log_audit
from app.schemas import LoginRequest, TokenResponse, RefreshTokenRequest, UserResponse
from app.services.email_service import get_email_service
from app.services.email_templates import DEFAULT_EMAIL_TEMPLATES
from app.core.config import settings
from app.services.rate_limiter import rate_limiter, RateLimitExceeded
import hashlib
import logging

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = logging.getLogger(__name__)


def _check_login_rate_limit(ip: str):
    """Enforce login attempt limit per IP (sliding window)."""
    allowed, retry_after = rate_limiter.check(
        f"login:{ip}", settings.RATE_LIMIT_LOGIN_LIMIT, settings.RATE_LIMIT_LOGIN_WINDOW
    )
    if not allowed:
        raise RateLimitExceeded(settings.RATE_LIMIT_LOGIN_LIMIT, retry_after, scope="login")


def _check_password_reset_rate_limit(email: str):
    """Enforce password-reset request limit per email (sliding window)."""
    allowed, retry_after = rate_limiter.check(
        f"reset:{email}", settings.RATE_LIMIT_RESET_LIMIT, settings.RATE_LIMIT_RESET_WINDOW
    )
    if not allowed:
        raise RateLimitExceeded(settings.RATE_LIMIT_RESET_LIMIT, retry_after, scope="password_reset")


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, http_request: Request, db: Session = Depends(get_db)):
    """Login with email and password, return access + refresh tokens."""
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


@router.post("/request-password-reset")
def request_password_reset(
    request: PasswordResetRequest,
    http_request: Request,
    db: Session = Depends(get_db)
):
    """Request a password reset token via email."""
    ip = http_request.client.host if http_request.client else "unknown"

    _check_password_reset_rate_limit(request.email)

    # Find user by email
    user = db.query(User).filter(
        User.email == request.email,
        User.is_active == True,
        User.deleted_at == None
    ).first()
    
    if not user:
        # For security, don't reveal if email exists
        logger.info("PASSWORD RESET requested for unknown email: %s from %s", request.email, ip)
        return {"message": "If email exists, a password reset link will be sent"}
    
    # Create reset token
    reset_token = create_password_reset_token(user.id, db)
    
    # Build reset link (frontend will handle the reset)
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
    
    # Send email with reset link
    email_service = get_email_service()
    template = DEFAULT_EMAIL_TEMPLATES["password_reset"]
    
    success = email_service.send_templated_email(
        to_email=user.email,
        template=template,
        context={
            "user_name": user.full_name or user.email.split('@')[0],
            "reset_link": reset_link
        }
    )
    
    if success:
        logger.info("PASSWORD RESET email sent to %s from %s", user.email, ip)
        log_audit(db, user_id=user.id, action="password_reset_requested", 
                  entity_type="user", entity_id=user.id, ip_address=ip)
    else:
        logger.error("PASSWORD RESET email failed for %s from %s", user.email, ip)
    
    return {"message": "If email exists, a password reset link will be sent"}


@router.post("/reset-password", response_model=PasswordResetResponse)
def reset_password(
    request: PasswordResetConfirm,
    http_request: Request,
    db: Session = Depends(get_db)
):
    """Reset password using a valid reset token."""
    ip = http_request.client.host if http_request.client else "unknown"
    
    # Verify the reset token
    user_id = verify_password_reset_token(request.token, db)
    
    if not user_id:
        logger.warning("PASSWORD RESET with invalid/expired token from %s", ip)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset link"
        )
    
    # Find user
    user = db.query(User).filter(
        User.id == user_id,
        User.is_active == True,
        User.deleted_at == None
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found"
        )
    
    # Update password
    user.password_hash = hash_password(request.new_password)
    db.commit()
    
    # Mark token as used
    mark_password_reset_token_used(request.token, db)
    
    # Create new access tokens for automatic login
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id, db)
    
    logger.info("PASSWORD RESET successful for %s from %s", user.email, ip)
    log_audit(db, user_id=user.id, action="password_reset_completed", 
              entity_type="user", entity_id=user.id, ip_address=ip)
    
    user_data = UserResponse.model_validate(user)
    
    return {
        "message": "Password reset successful. You are now logged in.",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user_data
    }

@router.get("/verify-reset-token", response_model=dict)
def verify_reset_token_endpoint(
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    """Verify a password reset token is valid and not expired."""
    user_id = verify_password_reset_token(token, db)
    if user_id:
        return {"valid": True, "user_id": user_id}
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid or expired password reset token"
    )
