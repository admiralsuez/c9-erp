"""User digital signature endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_user, require_admin
from app.models import User, UserSignature
from app.schemas import SignatureResponse, SignatureUpdate

router = APIRouter(prefix="/users", tags=["Users"])

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
