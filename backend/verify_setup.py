#!/usr/bin/env python3
"""Verify that the setup was successful."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load env
env_path = Path(".env.local")
if env_path.exists():
    load_dotenv(env_path)

from app.core.database import SessionLocal
from app.models import User

db = SessionLocal()

try:
    admin = db.query(User).filter(User.email == "admin@localhost.com").first()
    
    if admin:
        print("\n" + "="*60)
        print(" Setup Verification")
        print("="*60)
        print(f"\n[✓] Admin user found")
        print(f"    Email:    {admin.email}")
        print(f"    Name:     {admin.full_name}")
        print(f"    Role:     {admin.role.name if admin.role else 'No role'}")
        print(f"    Active:   {admin.is_active}")
        print(f"    Created:  {admin.created_at}")
        
        if admin.role and admin.role.name == "Admin":
            print("\n[✓] Admin has correct Admin role")
            print("\nYou can now:")
            print("  • Login with: admin@localhost.com / admin@123")
            print("  • Access backup features")
            print("  • Manage users and permissions")
            print("  • Configure system settings")
        else:
            print(f"\n[!] Warning: Admin role is '{admin.role.name if admin.role else 'None'}', expected 'Admin'")
    else:
        print("\n[✗] Admin user not found")
    
    print("\n" + "="*60 + "\n")
    
finally:
    db.close()
