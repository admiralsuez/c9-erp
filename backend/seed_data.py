"""
Seed database with initial data for Phase 1.
Run: python seed_data.py
"""

from app.core.database import SessionLocal, engine, Base
from app.models import (
    Role, Permission, RolePermission, User, Settings,
    Warehouse, WarehouseZone, WarehouseRack, WarehouseShelf, WarehouseBin,
    InventoryCategory, InventoryItem, Vendor
)
from decimal import Decimal
from datetime import datetime, timezone
from app.core.auth import hash_password

# Create tables
Base.metadata.create_all(bind=engine)

# Migration: add vendor_token_hash column if missing (for DBs created before it was in the model)
from sqlalchemy import inspect, text
inspector = inspect(engine)
vendor_columns = [c["name"] for c in inspector.get_columns("vendors")]
if "vendor_token_hash" not in vendor_columns:
    conn = engine.connect()
    conn.execute(text("ALTER TABLE vendors ADD COLUMN vendor_token_hash VARCHAR(64)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_vendor_token_hash ON vendors(vendor_token_hash)"))
    conn.commit()
    conn.close()
    print("[+] Added missing column: vendors.vendor_token_hash")

db = SessionLocal()

def seed_roles_and_permissions():
    """Create roles and permissions."""
    print("Seeding roles and permissions...")
    
    # Define permissions
    permissions_list = [
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
    for code, description in permissions_list:
        perm = db.query(Permission).filter(Permission.code == code).first()
        if not perm:
            perm = Permission(code=code, description=description)
            db.add(perm)
        permissions[code] = perm
    
    db.commit()
    
    # Define roles
    roles_list = [
        ("Admin", "Full system access", ["dashboard.view", "inventory.create", "inventory.edit", "inventory.dispatch", "orders.create", "orders.approve", "users.manage", "reports.view"]),
        ("Manager", "Manage inventory and orders (no user management)", ["dashboard.view", "inventory.create", "inventory.edit", "inventory.dispatch", "orders.create", "orders.approve", "reports.view"]),
        ("Warehouse User", "Restock and dispatch inventory", ["inventory.create", "inventory.dispatch"]),
        ("Viewer", "Read-only access", []),
    ]
    
    for role_name, description, perm_codes in roles_list:
        role = db.query(Role).filter(Role.name == role_name).first()
        if not role:
            role = Role(name=role_name, description=description)
            db.add(role)
            db.flush()
            
            for perm_code in perm_codes:
                if perm_code in permissions:
                    rp = RolePermission(role_id=role.id, permission_id=permissions[perm_code].id)
                    db.add(rp)
    
    db.commit()
    print("[+] Roles and permissions created")


def seed_users():
    """Create seed users."""
    print("Seeding users...")
    
    admin_role = db.query(Role).filter(Role.name == "Admin").first()
    manager_role = db.query(Role).filter(Role.name == "Manager").first()
    warehouse_role = db.query(Role).filter(Role.name == "Warehouse User").first()
    
    users_list = [
        ("Admin User", "admin@example.com", "admin@123", admin_role.id, "Admin"),
        ("John Manager", "manager@example.com", "manager123", manager_role.id, "Operations"),
        ("Raj Warehouse", "warehouse@example.com", "warehouse123", warehouse_role.id, "Warehouse"),
    ]
    
    for full_name, email, password, role_id, department in users_list:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                full_name=full_name,
                email=email,
                password_hash=hash_password(password),
                role_id=role_id,
                department=department
            )
            db.add(user)
    
    db.commit()
    print("[+] Users created")
    print("  - admin@example.com / admin@123")
    print("  - manager@example.com / manager123")
    print("  - warehouse@example.com / warehouse123")


def seed_settings():
    """Create default settings."""
    print("Seeding settings...")
    
    settings = db.query(Settings).first()
    if not settings:
        settings = Settings(
            company_name="Cloud9",
            company_gst="18AABCU1234F1Z0",
            company_address="123 Main St, Mumbai, MH 400001",
            company_contact="+91-22-1234-5678",
            order_number_format="ORD-{YYYY}-{SEQ}",
            requisition_number_format="REQ-{YYYY}-{SEQ}",
            pdf_header_text="Cloud9 - Official Purchase Order",
            pdf_footer_text="Thank you for your business!",
            default_low_stock_threshold=Decimal("10")
        )
        db.add(settings)
    
    db.commit()
    print("[+] Settings created")


def seed_warehouse_hierarchy():
    """Create warehouse structure."""
    print("Seeding warehouse hierarchy...")
    
    warehouse = db.query(Warehouse).filter(Warehouse.name == "Mumbai Warehouse").first()
    if not warehouse:
        warehouse = Warehouse(
            name="Mumbai Warehouse",
            address="Mumbai Port Authority, Mumbai, MH"
        )
        db.add(warehouse)
        db.flush()
        
        # Zone A
        zone_a = WarehouseZone(warehouse_id=warehouse.id, name="Zone A")
        db.add(zone_a)
        db.flush()
        
        # Rack 1
        rack_1 = WarehouseRack(zone_id=zone_a.id, name="Rack 1")
        db.add(rack_1)
        db.flush()
        
        # Shelf 1
        shelf_1 = WarehouseShelf(rack_id=rack_1.id, name="Shelf 1")
        db.add(shelf_1)
        db.flush()
        
        # Bins
        for i in range(1, 6):
            bin_obj = WarehouseBin(shelf_id=shelf_1.id, name=f"Bin {i}")
            db.add(bin_obj)
        
        db.commit()
    
    print("[+] Warehouse hierarchy created")


def seed_inventory_categories():
    """Create inventory categories."""
    print("Seeding inventory categories...")
    
    categories_list = [
        "Electronics",
        "Promotional Items",
        "Supplies",
        "Equipment",
    ]
    
    for cat_name in categories_list:
        cat = db.query(InventoryCategory).filter(InventoryCategory.name == cat_name).first()
        if not cat:
            cat = InventoryCategory(name=cat_name)
            db.add(cat)
    
    db.commit()
    print("[+] Inventory categories created")


def seed_vendors():
    """Create seed vendors."""
    print("Seeding vendors...")
    
    vendors_list = [
        ("ABC Traders", "abc traders", "Wholesale", "Rajesh Kumar", "+91-9876-543210", "rajesh@abctraders.com", "Mumbai"),
        ("XYZ Supplies", "xyz supplies", "Supplier", "Priya Singh", "+91-9876-543211", "priya@xyzsupplies.com", "Delhi"),
        ("Global Items Inc", "global items inc", "Wholesaler", "Mike Johnson", "+1-555-1234", "mike@globalitems.com", "USA"),
    ]           
    
    for name, normalized, vendor_type, contact, phone, email, city in vendors_list:
        vendor = db.query(Vendor).filter(Vendor.name_normalized == normalized).first()
        if not vendor:
            vendor = Vendor(
                name=name,
                name_normalized=normalized,
                vendor_type=vendor_type,
                contact_person=contact,
                phone=phone,
                email=email,
                city=city,
                state="Active" if city == "Mumbai" or city == "Delhi" else "USA"
            )
            db.add(vendor)
    
    db.commit()
    print("[+] Vendors created")


def seed_inventory_items():
    """Create seed inventory items."""
    print("Seeding inventory items...")
    
    warehouse = db.query(Warehouse).filter(Warehouse.name == "Mumbai Warehouse").first()
    zone = db.query(WarehouseZone).filter(WarehouseZone.warehouse_id == warehouse.id).first()
    rack = db.query(WarehouseRack).filter(WarehouseRack.zone_id == zone.id).first()
    shelf = db.query(WarehouseShelf).filter(WarehouseShelf.rack_id == rack.id).first()
    bins = db.query(WarehouseBin).filter(WarehouseBin.shelf_id == shelf.id).all()
    
    promo_cat = db.query(InventoryCategory).filter(InventoryCategory.name == "Promotional Items").first()
    
    items_list = [
        ("Promotional Sticker Pack", "SKU-001", "8901234567890", "consumable", 500, 50, bins[0].id if bins else None),
        ("Black Umbrella - Returnable", "SKU-002", "8901234567891", "returnable", 100, 20, bins[1].id if len(bins) > 1 else None),
        ("LED Glow Sign", "SKU-003", "8901234567892", "returnable", 50, 10, bins[2].id if len(bins) > 2 else None),
        ("Acrylic Stand", "SKU-004", "8901234567893", "returnable", 75, 15, bins[3].id if len(bins) > 3 else None),
        ("Bar Mat - Rubber", "SKU-005", "8901234567894", "returnable", 200, 25, bins[4].id if len(bins) > 4 else None),
    ]
    
    for name, sku, barcode, item_type, quantity, min_qty, bin_id in items_list:
        item = db.query(InventoryItem).filter(InventoryItem.sku == sku).first()
        if not item:
            item = InventoryItem(
                name=name,
                sku=sku,
                barcode=barcode,
                qr_code_data=barcode,
                category_id=promo_cat.id if promo_cat else None,
                item_type=item_type,
                current_quantity=Decimal(str(quantity)),
                reserved_quantity=Decimal("0"),
                minimum_quantity=Decimal(str(min_qty)),
                bin_id=bin_id,
                description=f"Sample {item_type} item"
            )
            db.add(item)
    
    db.commit()
    print("[+] Inventory items created")


def get_or_create_admin():
    """Ensure at least one admin user exists (for first-time setup)."""
    print("Checking for Admin user...")
    
    admin_role = db.query(Role).filter(Role.name == "Admin").first()
    admin_user = db.query(User).filter(User.role_id == admin_role.id).first() if admin_role else None
    
    if not admin_user:
        print("[!] No Admin user found. Creating initial admin account...")
        if not admin_role:
            admin_role = Role(name="Admin", description="Full system access")
            db.add(admin_role)
            db.flush()
        
        admin_user = User(
            full_name="System Administrator",
            email="vibin.cloud9@gmail.com",
            password_hash=hash_password("admin@123"),
            role_id=admin_role.id,
            department="Administration"
        )
        db.add(admin_user)
        db.commit()
        print("[+] Initial Admin user created: vibin.cloud9@gmail.com / admin@123")
        return True
    else:
        print(f"[✓] Admin user exists: {admin_user.email}")
        return False


def main():
    """Run all seed functions."""
    print("\n" + "="*60)
    print("Cloud9 ERP Database Setup")
    print("="*60 + "\n")
    
    try:
        # First ensure an admin exists (for first-time users)
        admin_created = False
        try:
            admin_role = db.query(Role).filter(Role.name == "Admin").first()
            if not admin_role:
                print("[*] First-time setup detected. Creating initial role and admin user...")
                seed_roles_and_permissions()
                admin_created = get_or_create_admin()
            else:
                admin_created = get_or_create_admin()
        except Exception as e:
            print(f"[*] Setting up roles and permissions...")
            seed_roles_and_permissions()
            admin_created = get_or_create_admin()
        
        # Then run standard seed functions
        seed_users()
        seed_settings()
        seed_warehouse_hierarchy()
        seed_inventory_categories()
        seed_vendors()
        seed_inventory_items()
        
        print("\n" + "="*60)
        print("[+] Database setup completed successfully!")
        print("="*60 + "\n")
        
        if admin_created:
            print("🔐 FIRST-TIME SETUP - Admin Account Created")
            print("   Email: vibin.cloud9@gmail.com")
            print("   Password: admin@123")
            print("\n   ⚠️  IMPORTANT: Change this password in Settings after first login!\n")
        
        print("Test Credentials:")
        print("  ├─ Admin: admin@example.com / admin@123")
        print("  ├─ Manager: manager@example.com / manager123")
        print("  └─ Warehouse: warehouse@example.com / warehouse123")
        print("\nAdditional Setup Credentials:")
        print("  └─ Initial Admin: vibin.cloud9@gmail.com / admin@123")
        print()
        print("Features now available:")
        print("  ✓ Dashboard & Analytics")
        print("  ✓ Inventory Management")
        print("  ✓ Order Management with Approval Matrix")
        print("  ✓ User & Permission Management")
        print("  ✓ Warehouse Structure")
        print("  ✓ Backup & Restore (Admin only)")
        print()
        
    except Exception as e:
        print(f"\n[-] Error during setup: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
