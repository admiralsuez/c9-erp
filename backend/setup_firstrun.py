#!/usr/bin/env python3
"""
Cloud9 ERP - First Run Setup Script
Creates initial database and admin user for first-time deployment.

Usage:
    python setup_firstrun.py

This script will:
1. Create all database tables
2. Set up roles and permissions
3. Create an initial Admin user (if none exists)
4. Show you the login credentials
"""

import os
import sys
from pathlib import Path

# Load environment from .env.local ONLY if DATABASE_URL is not already set
# (Prevents stale local config from shadowing production env vars)
if not os.getenv("DATABASE_URL"):
    env_path = Path(__file__).parent / ".env.local"
    if env_path.exists():
        from dotenv import load_dotenv
        load_dotenv(env_path)
        print("[*] Loaded .env.local (DATABASE_URL was not set)")
else:
    print("[*] DATABASE_URL already set in environment; skipping .env.local")

from app.core.database import SessionLocal, engine, Base
from app.models import Role, User, Permission, RolePermission, Settings
from app.core.auth import hash_password
from app.core.config import settings
from decimal import Decimal

# Log which database we're connecting to (host only, password redacted)
db_url = settings.DATABASE_URL
if "@" in db_url:
    # Redact password: postgresql://user:PASSWORD@host:port/db
    parts = db_url.split("@")
    db_display = f"{parts[0].split(':')[0]}://***@{parts[1]}"
else:
    db_display = db_url
print(f"[*] Using database: {db_display}")

def create_tables():
    """Create all database tables."""
    print("[*] Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("[✓] Database tables created")
        return True
    except Exception as e:
        print(f"[✗] Error creating tables: {e}")
        return False

def setup_roles_permissions(db):
    """Create roles and permissions."""
    print("[*] Setting up roles and permissions...")
    
    try:
        # Check if Admin role exists
        admin_role = db.query(Role).filter(Role.name == "Admin").first()
        if admin_role:
            print("[✓] Admin role already exists")
            return True
        
        # Create permissions
        permissions_data = [
            ("dashboard.view", "View analytics dashboard"),
            ("inventory.create", "Create inventory items"),
            ("inventory.edit", "Edit inventory"),
            ("inventory.dispatch", "Dispatch inventory"),
            ("orders.create", "Create orders"),
            ("orders.approve", "Approve orders"),
            ("users.manage", "Manage users"),
            ("reports.view", "View reports"),
        ]
        
        permissions = {}
        for code, desc in permissions_data:
            perm = db.query(Permission).filter(Permission.code == code).first()
            if not perm:
                perm = Permission(code=code, description=desc)
                db.add(perm)
            permissions[code] = perm
        
        db.commit()
        
        # Create Admin role with all permissions
        admin_role = Role(
            name="Admin",
            description="Full system access and administration"
        )
        db.add(admin_role)
        db.flush()
        
        for perm in permissions.values():
            rp = RolePermission(role_id=admin_role.id, permission_id=perm.id)
            db.add(rp)
        
        db.commit()
        print("[✓] Roles and permissions created")
        return True
        
    except Exception as e:
        print(f"[✗] Error setting up roles: {e}")
        db.rollback()
        return False

def create_admin_user(db, email="admin@localhost", password="admin@123"):
    """Create initial admin user."""
    print("[*] Checking for admin user...")
    
    try:
        # Check if admin already exists
        admin_user = db.query(User).filter(User.email == email).first()
        if admin_user:
            print(f"[✓] Admin user already exists: {email}")
            return email, password, False
        
        # Get Admin role
        admin_role = db.query(Role).filter(Role.name == "Admin").first()
        if not admin_role:
            print("[✗] Admin role not found. Run setup_roles_permissions first.")
            return None, None, False
        
        # Create admin user
        admin_user = User(
            full_name="System Administrator",
            email=email,
            password_hash=hash_password(password),
            role_id=admin_role.id,
            department="Administration",
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        
        print(f"[✓] Admin user created: {email}")
        return email, password, True
        
    except Exception as e:
        print(f"[✗] Error creating admin user: {e}")
        db.rollback()
        return None, None, False

def setup_default_settings(db):
    """Create default settings if none exist."""
    print("[*] Setting up default settings...")
    
    try:
        settings = db.query(Settings).first()
        if settings:
            print("[✓] Settings already configured")
            return True
        
        settings = Settings(
            company_name="Cloud9 ERP",
            company_gst="00AABCT1234H1Z0",
            company_address="Your Company Address",
            company_contact="+91-XXXX-XXXX",
            order_number_format="ORD-{YYYY}-{SEQ}",
            requisition_number_format="REQ-{YYYY}-{SEQ}",
            pdf_header_text="Cloud9 ERP - Purchase Order",
            pdf_footer_text="Thank you for your business!",
            default_low_stock_threshold=Decimal("10")
        )
        db.add(settings)
        db.commit()
        print("[✓] Default settings created")
        return True
        
    except Exception as e:
        print(f"[✗] Error setting up settings: {e}")
        db.rollback()
        return False

def main():
    """Main setup function."""
    print("\n" + "="*70)
    print(" Cloud9 ERP - First Run Setup")
    print("="*70 + "\n")
    
    db = SessionLocal()
    success = True
    
    try:
        # Step 1: Create tables
        if not create_tables():
            success = False
            raise Exception("Failed to create database tables")
        
        # Step 2: Setup roles and permissions
        if not setup_roles_permissions(db):
            success = False
            raise Exception("Failed to setup roles and permissions")
        
        # Step 3: Create admin user
        admin_email, admin_password, admin_created = create_admin_user(db)
        if admin_email is None:
            success = False
            raise Exception("Failed to create admin user")
        
        # Step 4: Setup default settings
        if not setup_default_settings(db):
            success = False
            raise Exception("Failed to setup default settings")
        
        # Success message
        print("\n" + "="*70)
        if admin_created:
            print(" ✓ First-time setup completed successfully!")
            print("="*70)
            print("\n🔐 LOGIN CREDENTIALS\n")
            print(f"   Email:    {admin_email}")
            print(f"   Password: {admin_password}")
            print("\n⚠️  IMPORTANT SECURITY NOTES:\n")
            print("   1. Change this password immediately after first login")
            print("   2. Go to Settings → Users to create additional accounts")
            print("   3. Set up your company details in Settings → Company Profile")
            print("   4. Create your warehouse structure in Settings → Warehouse")
            print("\n📋 NEXT STEPS:\n")
            print("   1. Start the backend: python main.py")
            print("   2. Start the frontend: npm run dev")
            print("   3. Navigate to http://localhost:5173")
            print("   4. Login with the credentials above")
            print("   5. Update company information and warehouse structure")
        else:
            print(" ✓ Setup verification completed")
            print("="*70)
            print(f"\n   Admin user already exists: {admin_email}")
            print("   Database is ready to use!")
        
        print("\n" + "="*70 + "\n")
        
    except Exception as e:
        print(f"\n[✗] Setup failed: {e}")
        success = False
    finally:
        db.close()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
