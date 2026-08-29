#!/usr/bin/env python3
"""
Grant vendors.create permission to all existing roles.
Run this after the first-run setup to ensure all roles have the permission.
"""

import os
import sys
from pathlib import Path

# Load environment from .env.local ONLY if DATABASE_URL is not already set
if not os.getenv("DATABASE_URL"):
    env_path = Path(__file__).parent / ".env.local"
    if env_path.exists():
        from dotenv import load_dotenv
        load_dotenv(env_path)
        print("[*] Loaded .env.local (DATABASE_URL was not set)")
else:
    print("[*] DATABASE_URL already set in environment; skipping .env.local")

from app.core.database import SessionLocal
from app.models import Role, Permission, RolePermission
from app.core.config import settings

# Log which database we're connecting to
db_url = settings.DATABASE_URL
if "@" in db_url:
    parts = db_url.split("@")
    db_display = f"{parts[0].split(':')[0]}://***@{parts[1]}"
else:
    db_display = db_url
print(f"[*] Using database: {db_display}")

def grant_vendor_permission():
    """Grant vendors.create permission to all roles."""
    db = SessionLocal()
    
    try:
        # Get or create vendors.create permission
        perm = db.query(Permission).filter(Permission.code == "vendors.create").first()
        if not perm:
            perm = Permission(code="vendors.create", description="Create vendors")
            db.add(perm)
            db.commit()
            print("[✓] Created vendors.create permission")
        else:
            print("[✓] vendors.create permission already exists")
        
        # Get all roles
        roles = db.query(Role).all()
        if not roles:
            print("[!] No roles found in database")
            return False
        
        print(f"[*] Found {len(roles)} role(s)")
        
        # Grant permission to each role
        for role in roles:
            # Check if role already has this permission
            existing = db.query(RolePermission).filter(
                RolePermission.role_id == role.id,
                RolePermission.permission_id == perm.id
            ).first()
            
            if not existing:
                rp = RolePermission(role_id=role.id, permission_id=perm.id)
                db.add(rp)
                print(f"   [✓] Granted vendors.create to role: {role.name}")
            else:
                print(f"   [✓] Role '{role.name}' already has vendors.create")
        
        db.commit()
        print("\n[✓] Permission granted to all roles successfully")
        return True
        
    except Exception as e:
        print(f"[✗] Error: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("\n" + "="*70)
    print(" Grant vendors.create Permission to All Roles")
    print("="*70 + "\n")
    
    success = grant_vendor_permission()
    
    print("\n" + "="*70 + "\n")
    sys.exit(0 if success else 1)
