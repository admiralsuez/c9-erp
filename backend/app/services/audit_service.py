from sqlalchemy.orm import Session
from app.models import AuditLog
from datetime import datetime, timezone


def log_audit(
    db: Session,
    user_id: int,
    action: str,
    entity_type: str = None,
    entity_id: int = None,
    ip_address: str = None,
    previous_value: dict = None,
    new_value: dict = None,
    reason: str = None,
):
    entry = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        ip_address=ip_address,
        previous_value=previous_value,
        new_value=new_value,
        reason=reason,
        created_at=datetime.now(timezone.utc),
    )
    db.add(entry)
