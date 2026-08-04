#!/usr/bin/env python
"""
Quick seed script - simpler version with better error handling.
Run: python quick_seed.py
"""

from app.core.database import SessionLocal, engine, Base
from app.models import Role, Permission, RolePermission, User
from app.core.auth import hash_password

print("\n" + "="*60)
print("Quick Cloud9 ERP Seed")
print("="*60)

# Create all tables
print("\n[*] Creating database tables...")
try:
    Base.metadata.create_all(bind=engine)
    print("[✓] Tables created successfully")
except Exception as e:
    print(f"[!] Error creating tables: {e}")
    exit(1)

db = SessionLocal()

try:
    # 1. Create permissions
    print("\n[*] Creating permissions...")
    permissions_data = [
        ("dashboard.view", "View analytics dashboard"),
        ("inventory.create", "Create inventory items and categories"),
        ("inventory.edit", "Edit and adjust inventory"),
        ("inventory.dispatch", "Dispatch and restock inventory"),
        ("orders.create", "Create orders"),
        ("orders.approve", "Approve orders"),
        ("users.manage", "Manage users"),
        ("reports.view", "View reports"),
    ]
    
    permissions = {}
    for code, desc in permissions_data:
        existing = db.query(Permission).filter(Permission.code == code).first()
        if not existing:
            perm = Permission(code=code, description=desc)
            db.add(perm)
            db.flush()
            permissions[code] = perm
            print(f"  ✓ Created permission: {code}")
        else:
            permissions[code] = existing
    
    db.commit()
    
    # 2. Create roles
    print("\n[*] Creating roles...")
    roles_data = [
        ("Admin", "Full system access", ["dashboard.view", "inventory.create", "inventory.edit", "inventory.dispatch", "orders.create", "orders.approve", "users.manage", "reports.view"]),
        ("Manager", "Manage inventory and orders", ["dashboard.view", "inventory.create", "inventory.edit", "inventory.dispatch", "orders.create", "orders.approve", "reports.view"]),
        ("Warehouse User", "Restock and dispatch inventory", ["inventory.create", "inventory.dispatch"]),
        ("Viewer", "Read-only access", []),
    ]
    
    roles = {}
    for role_name, desc, perm_codes in roles_data:
        existing = db.query(Role).filter(Role.name == role_name).first()
        if not existing:
            role = Role(name=role_name, description=desc)
            db.add(role)
            db.flush()
            roles[role_name] = role
            
            # Add permissions
            for perm_code in perm_codes:
                if perm_code in permissions:
                    rp = RolePermission(role_id=role.id, permission_id=permissions[perm_code].id)
                    db.add(rp)
            
            db.flush()
            print(f"  ✓ Created role: {role_name}")
        else:
            roles[role_name] = existing
    
    db.commit()
    
    # 3. Create admin user
    print("\n[*] Creating admin user...")
    existing_admin = db.query(User).filter(User.email == "admin@thecloud9corp.com").first()
    if not existing_admin:
        admin = User(
            full_name="System Administrator",
            email="admin@thecloud9corp.com",
            password_hash=hash_password("Admin@12345"),
            role_id=roles["Admin"].id,
            department="Administration"
        )
        db.add(admin)
        db.commit()
        print(f"  ✓ Created admin user: admin@thecloud9corp.com / Admin@12345")
    else:
        print(f"  ℹ Admin user already exists: {existing_admin.email}")
    
    print("\n" + "="*60)
    print("[✓] Seed completed successfully!")
    print("="*60)
    print("\nYour admin user now has inventory.create permission.")
    print("Try creating an inventory item again - it should work now!")
    print()

except Exception as e:
    print(f"\n[✗] Error: {e}")
    import traceback
    traceback.print_exc()
    db.rollback()
finally:
    db.close()
