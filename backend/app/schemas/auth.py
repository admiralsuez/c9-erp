from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict, Field
from datetime import datetime


# ============ AUTH ============
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserBase(BaseModel):
    full_name: str
    email: EmailStr
    department: Optional[str] = None
    location: str = "HO"


class PermissionSchema(BaseModel):
    id: int
    code: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RoleSchema(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    permissions: List[PermissionSchema] = []

    model_config = ConfigDict(from_attributes=True)


class UserResponse(UserBase):
    id: int
    email: str
    role: Optional[RoleSchema] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: Optional[UserResponse] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# ============ USERS & ROLES ============
class RoleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    permission_ids: List[int] = []


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permission_ids: Optional[List[int]] = None


class UserCreate(UserBase):
    password: str
    role_id: int


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    department: Optional[str] = None
    role_id: Optional[int] = None
    location: Optional[str] = None


# ============ PASSWORD RESET ============
class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, description="Password must be at least 8 characters")


class PasswordResetResponse(BaseModel):
    message: str
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: Optional[UserResponse] = None


# ============ USER SIGNATURE ============
class SignatureResponse(BaseModel):
    id: int
    user_id: int
    signature_data: str
    uploaded_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SignatureUpdate(BaseModel):
    signature_data: str
