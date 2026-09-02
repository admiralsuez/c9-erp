"""
One-off migration: grant new permissions to existing roles.

Phase 0.2 hardening adds require_permission() guards on order state
transitions and vendor CRUD. This script ensures existing roles in the
database are updated to include the new permission codes so existing
users (especially Admin/Manager) are not locked out.

Run once after deploying the Phase 0.2 backend changes:
    cd /root/apps/c9-erp
    docker compose -f docker-compose.production.yml exec backend python /app/grant_phase0_permissions.py
"""
import os
import sys
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models import Permission, Role, RolePermission


NEW_PERMISSIONS = [
    ("vendors.edit", "Edit vendors"),
    ("vendors.delete", "Delete vendors"),
    ("inventory.restock", "Restock inventory"),
    ("orders.cancel", "Cancel orders"),
    ("orders.dispatch", "Dispatch orders"),
    ("orders.deliver", "Mark orders delivered"),
    ("orders.close", "Close orders"),
    ("orders.return", "Process order returns"),
    ("orders.manage", "Manage order details"),
]


# Map of role name -> list of permission codes to grant
ROLE_PERMISSION_GRANTS = {
    "Admin": [
        "vendors.edit", "vendors.delete", "inventory.restock",
        "orders.cancel", "orders.dispatch", "orders.deliver",
        "orders.close", "orders.return", "orders.manage",
    ],
    "Manager": [
        "vendors.edit", "inventory.restock",
        "orders.cancel", "orders.dispatch", "orders.deliver",
        "orders.close", "orders.return", "orders.manage",
    ],
    "Warehouse User": ["inventory.restock"],
}


def ensure_permissions(db: Session) -> dict:
    """Create any missing Permission rows; return code -> Permission."""
    perms = {}
    for code, desc in NEW_PERMISSIONS:
        perm = db.query(Permission).filter(Permission.code == code).first()
        if not perm:
            perm = Permission(code=code, description=desc)
            db.add(perm)
            print(f"[+] Created permission: {code}")
        perms[code] = perm
    db.commit()
    return perms


def grant_to_role(db: Session, role_name: str, perm_codes: list, perms: dict) -> int:
    role = db.query(Role).filter(Role.name == role_name).first()
    if not role:
        print(f"[!] Role '{role_name}' not found; skipping")
        return 0
    granted = 0
    for code in perm_codes:
        perm = perms.get(code)
        if not perm:
            continue
        existing = db.query(RolePermission).filter(
            RolePermission.role_id == role.id,
            RolePermission.permission_id == perm.id,
        ).first()
        if existing:
            continue
        db.add(RolePermission(role_id=role.id, permission_id=perm.id))
        granted += 1
    db.commit()
    return granted


def main():
    print("=" * 60)
    print(" Phase 0.2 permission migration")
    print("=" * 60)

    db = SessionLocal()
    try:
        perms = ensure_permissions(db)

        total_granted = 0
        for role_name, codes in ROLE_PERMISSION_GRANTS.items():
            granted = grant_to_role(db, role_name, codes, perms)
            print(f"[✓] Granted {granted} new permission(s) to role '{role_name}'")
            total_granted += granted

        print(f"\n[✓] Total permissions granted: {total_granted}")
        print("=" * 60)
    except Exception as e:
        print(f"[✗] Error: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
