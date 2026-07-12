from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_user, require_admin
from app.models import ApprovalRule, User, Role
from app.schemas import ApprovalRuleCreateRequest, ApprovalRuleResponse
from typing import List

router = APIRouter(prefix="/approval-rules", tags=["Approval"])


@router.get("", response_model=List[ApprovalRuleResponse])
def list_approval_rules(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """List all approval rules (admin only)."""
    skip = (page - 1) * size
    rules = db.query(ApprovalRule).order_by(ApprovalRule.priority).offset(skip).limit(size).all()
    return rules


@router.post("", response_model=ApprovalRuleResponse, status_code=status.HTTP_201_CREATED)
def create_approval_rule(
    rule_data: ApprovalRuleCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create a new approval rule (admin only)."""
    # Verify approver role/user if specified
    if rule_data.approver_role_id:
        role = db.query(Role).filter(Role.id == rule_data.approver_role_id).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Approver role not found"
            )
    
    if rule_data.approver_user_id:
        user = db.query(User).filter(User.id == rule_data.approver_user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Approver user not found"
            )
    
    rule = ApprovalRule(
        name=rule_data.name,
        rule_type=rule_data.rule_type,
        condition_json=rule_data.condition_json,
        approver_role_id=rule_data.approver_role_id,
        approver_user_id=rule_data.approver_user_id,
        priority=rule_data.priority
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.get("/{rule_id}", response_model=ApprovalRuleResponse)
def get_approval_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get an approval rule by ID."""
    rule = db.query(ApprovalRule).filter(ApprovalRule.id == rule_id).first()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval rule not found"
        )
    
    return rule


@router.patch("/{rule_id}", response_model=ApprovalRuleResponse)
def update_approval_rule(
    rule_id: int,
    rule_data: ApprovalRuleCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update an approval rule."""
    rule = db.query(ApprovalRule).filter(ApprovalRule.id == rule_id).first()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval rule not found"
        )
    
    rule.name = rule_data.name
    rule.rule_type = rule_data.rule_type
    rule.condition_json = rule_data.condition_json
    rule.approver_role_id = rule_data.approver_role_id
    rule.approver_user_id = rule_data.approver_user_id
    rule.priority = rule_data.priority
    
    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_approval_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Delete an approval rule."""
    rule = db.query(ApprovalRule).filter(ApprovalRule.id == rule_id).first()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval rule not found"
        )
    
    db.delete(rule)
    db.commit()
