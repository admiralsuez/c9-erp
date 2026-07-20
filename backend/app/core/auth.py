from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.models import User, RefreshToken
import hashlib
import secrets as _secrets

security = HTTPBearer()


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    password_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    # bcrypt hashes start with $2b$ or $2a$
    if hashed_password.startswith(('$2b$', '$2a$', '$2y$')):
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    # Legacy SHA-256 hashes (from before bcrypt migration)
    # Use constant-time comparison to prevent timing attacks
    expected = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()
    return _secrets.compare_digest(expected, hashed_password)


def create_access_token(user_id: int, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    
    to_encode = {"sub": str(user_id), "exp": expire}
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(user_id: int, db: Session) -> str:
    """Create a refresh token with jti and exp, store hash in database."""
    token_id = _secrets.token_urlsafe(16)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRATION_DAYS)
    
    token = jwt.encode(
        {
            "sub": str(user_id),
            "type": "refresh",
            "jti": token_id,
            "exp": expires_at,
        },
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )
    
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    refresh_token = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
        revoked=False
    )
    db.add(refresh_token)
    db.commit()
    return token


def verify_token(token: str) -> dict:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return {"user_id": int(user_id)}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> User:
    """Get the current authenticated user from the token."""
    token = credentials.credentials
    payload = verify_token(token)
    user_id = payload.get("user_id")
    
    user = db.query(User).filter(User.id == user_id, User.is_active == True, User.deleted_at == None).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    
    return user


def require_permission(permission_code: str):
    """Decorator to require a specific permission."""
    async def permission_checker(current_user: User = Depends(get_current_user)):
        if not current_user.role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User has no role assigned")
        
        has_permission = any(
            p.code == permission_code for p in current_user.role.permissions
        )
        
        if not has_permission:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Permission '{permission_code}' required")
        
        return current_user
    
    return permission_checker


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require Admin role."""
    if not current_user.role or current_user.role.name != "Admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return current_user


def require_roles(*roles: str):
    """Decorator to require one of several roles."""
    async def role_checker(current_user: User = Depends(get_current_user)):
        if not current_user.role or current_user.role.name not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"One of roles {roles} required")
        return current_user
    
    return role_checker
