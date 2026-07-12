from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import desc, func
from app.core.database import get_db
from app.core.auth import get_current_user, require_admin, hash_password
from app.models import User, Role, Permission, UserSignature
from app.schemas import (
    UserCreate, UserUpdate, UserResponse,
    RoleSchema, RoleCreate, RoleUpdate,
    PermissionSchema, SignatureResponse, SignatureUpdate
)
from typing import List
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
    total = query.count()
    skip = (page - 1) * size
    users = query.offset(skip).limit(size).all()
    pages = (total + size - 1) // size if total > 0 else 1
    
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


@router.get("/roles/list", response_model=List[RoleSchema], tags=["Roles"])
def list_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all available roles (authenticated users only)."""
    roles = db.query(Role).all()
    return roles


@router.get("/permissions/list", response_model=List[PermissionSchema], tags=["Permissions"])
def list_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all available permissions (authenticated users only)."""
    permissions = db.query(Permission).all()
    return permissions


# ============ ROLE CRUD ============

@router.post("/roles", response_model=RoleSchema, status_code=status.HTTP_201_CREATED, tags=["Roles"])
def create_role(
    role_data: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create a new role with permissions (admin only)."""
    existing = db.query(Role).filter(Role.name == role_data.name).first()
    if existing:
        raise HTTPException(status_code=409, detail="Role with this name already exists")
    permissions = db.query(Permission).filter(Permission.id.in_(role_data.permission_ids)).all() if role_data.permission_ids else []
    role = Role(name=role_data.name, description=role_data.description)
    role.permissions = permissions
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


@router.patch("/roles/{role_id}", response_model=RoleSchema, tags=["Roles"])
def update_role(
    role_id: int,
    role_data: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update a role's name, description, or permissions (admin only)."""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    if role_data.name is not None:
        existing = db.query(Role).filter(Role.name == role_data.name, Role.id != role_id).first()
        if existing:
            raise HTTPException(status_code=409, detail="Role with this name already exists")
        role.name = role_data.name
    if role_data.description is not None:
        role.description = role_data.description
    if role_data.permission_ids is not None:
        permissions = db.query(Permission).filter(Permission.id.in_(role_data.permission_ids)).all()
        role.permissions = permissions
    db.commit()
    db.refresh(role)
    return role


@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Roles"])
def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Delete a role (admin only). Prevents deleting if users are assigned."""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    user_count = db.query(func.count(User.id)).filter(User.role_id == role_id, User.deleted_at == None).scalar() or 0
    if user_count > 0:
        raise HTTPException(status_code=409, detail=f"Cannot delete role: {user_count} user(s) are assigned to it")
    db.delete(role)
    db.commit()


# ============ USER SIGNATURE ============

@router.get("/{user_id}/signature", response_model=SignatureResponse)
def get_user_signature(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's digital signature. Users can see their own; admins can see any."""
    if current_user.id != user_id:
        require_admin(current_user)
    
    signature = db.query(UserSignature).filter(
        UserSignature.user_id == user_id
    ).first()
    
    if not signature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Signature not found"
        )
    
    return signature


@router.put("/{user_id}/signature", response_model=SignatureResponse)
def upsert_user_signature(
    user_id: int,
    signature_data: SignatureUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create or update user's digital signature. Users can update own; admins can update any."""
    if current_user.id != user_id:
        require_admin(current_user)
    
    user = db.query(User).filter(User.id == user_id, User.deleted_at == None).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    signature = db.query(UserSignature).filter(
        UserSignature.user_id == user_id
    ).first()
    
    if signature:
        signature.signature_data = signature_data.signature_data
    else:
        signature = UserSignature(
            user_id=user_id,
            signature_data=signature_data.signature_data
        )
        db.add(signature)
    
    db.commit()
    db.refresh(signature)
    return signature


@router.delete("/{user_id}/signature", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_signature(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete user's digital signature."""
    if current_user.id != user_id:
        require_admin(current_user)
    
    signature = db.query(UserSignature).filter(
        UserSignature.user_id == user_id
    ).first()
    
    if not signature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Signature not found"
        )
    
    db.delete(signature)
    db.commit()
