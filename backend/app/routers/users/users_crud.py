"""User CRUD endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, selectinload
from app.core.database import get_db
from app.core.auth import get_current_user, require_admin, hash_password
from app.models import User, Role
from app.schemas import UserCreate, UserUpdate, UserResponse
from app.services.pagination_utils import paginate_query, total_pages
from datetime import datetime, timezone

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("")
def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all active users (authenticated users) - returns paginated response."""
    query = db.query(User).options(
        selectinload(User.role).selectinload(Role.permissions)
    ).filter(User.deleted_at == None)
    sliced, page, size, total = paginate_query(query, page, size)

    users = sliced.all()
    pages = total_pages(total, size) or 1

    return {
        "items": [UserResponse.model_validate(u) for u in users],
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }

@router.get("/approvers", tags=["Users"])
def list_approvers(
    page: int = Query(1, ge=1),
    size: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List active users who can approve orders (authenticated users).
    Returns all active users with basic info for approver selection.
    """
    query = db.query(User).options(
        selectinload(User.role)
    ).filter(
        User.deleted_at == None,
        User.is_active == True
    )
    total = query.count()
    skip = (page - 1) * size
    users = query.offset(skip).limit(size).all()
    pages = (total + size - 1) // size if total > 0 else 1
    
    return {
        "items": [
            {
                "id": u.id,
                "full_name": u.full_name,
                "email": u.email,
                "department": u.department,
                "role_id": u.role_id,
                "role_name": u.role.name if u.role else None,
            }
            for u in users
        ],
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }

@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create a new user (admin only)."""
    # Check if user already exists
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists"
        )
    
    # Verify role exists
    role = db.query(Role).filter(Role.id == user_data.role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    user = User(
        full_name=user_data.full_name,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        role_id=user_data.role_id,
        department=user_data.department
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a user by ID."""
    user = db.query(User).filter(
        User.id == user_id,
        User.deleted_at == None
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update a user (admin only)."""
    user = db.query(User).filter(
        User.id == user_id,
        User.deleted_at == None
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields if provided
    if user_data.full_name:
        user.full_name = user_data.full_name
    if user_data.email:
        # Check if email is already used
        existing = db.query(User).filter(
            User.email == user_data.email,
            User.id != user_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already in use"
            )
        user.email = user_data.email
    if user_data.department:
        user.department = user_data.department
    if user_data.role_id:
        role = db.query(Role).filter(Role.id == user_data.role_id).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )
        user.role_id = user_data.role_id
    
    db.commit()
    db.refresh(user)
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Soft delete a user (admin only)."""
    user = db.query(User).filter(
        User.id == user_id,
        User.deleted_at == None
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.deleted_at = datetime.now(timezone.utc)
    db.commit()

@router.post("/{user_id}/restore", response_model=UserResponse)
def restore_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Restore a soft-deleted user (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.deleted_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not deleted"
        )
    
    user.deleted_at = None
    db.commit()
    db.refresh(user)
    return user
