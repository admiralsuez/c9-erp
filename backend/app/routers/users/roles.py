"""Role and permission management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.core.auth import get_current_user, require_admin
from app.models import User, Role, Permission
from app.schemas import RoleSchema, RoleCreate, RoleUpdate, PermissionSchema
from typing import List

router = APIRouter(prefix="/users", tags=["Users"])

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
