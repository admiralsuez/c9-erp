#!/usr/bin/env python
"""
Cloud9 ERP - Local Development Server
Runs all 7 phases with SQLite database for comprehensive testing
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from dotenv import load_dotenv

# Load local environment
env_file = Path(__file__).parent / ".env.local"
if env_file.exists():
    load_dotenv(env_file)
else:
    print(f"⚠️  {env_file} not found. Using default settings.")
    load_dotenv()

# Ensure SQLite is used for local development
if "sqlite" not in os.getenv("DATABASE_URL", "").lower():
    os.environ["DATABASE_URL"] = "sqlite:///./erp_local.db"

def setup_database():
    """Initialize database schema and seed data"""
    print("\n" + "="*60)
    print("[*] Setting up database...")
    print("="*60)
    
    try:
        # Import and run table creation
        from app.core.database import Base, engine
        from app import models  # This imports all model definitions
        from sqlalchemy import inspect, text
        
        print("[+] Creating database tables...")
        Base.metadata.create_all(bind=engine)
        
        # Migration: add vendor_token_hash column if missing
        inspector = inspect(engine)
        vendor_columns = [c["name"] for c in inspector.get_columns("vendors")]
        if "vendor_token_hash" not in vendor_columns:
            conn = engine.connect()
            conn.execute(text("ALTER TABLE vendors ADD COLUMN vendor_token_hash VARCHAR(64)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_vendor_token_hash ON vendors(vendor_token_hash)"))
            conn.commit()
            conn.close()
            print("[+] Added missing column: vendors.vendor_token_hash")
        
        # Migration: add location column to users if missing
        user_columns = [c["name"] for c in inspector.get_columns("users")]
        if "location" not in user_columns:
            conn = engine.connect()
            conn.execute(text("ALTER TABLE users ADD COLUMN location VARCHAR(10) DEFAULT 'HO'"))
            conn.commit()
            conn.close()
            print("[+] Added missing column: users.location")

        # Migration: add prefix columns to settings if missing
        if "settings" in inspector.get_table_names():
            settings_columns = [c["name"] for c in inspector.get_columns("settings")]
            conn = engine.connect()
            if "ho_prefix" not in settings_columns:
                conn.execute(text("ALTER TABLE settings ADD COLUMN ho_prefix VARCHAR(10) DEFAULT 'HO'"))
                print("[+] Added missing column: settings.ho_prefix")
            if "llf_prefix" not in settings_columns:
                conn.execute(text("ALTER TABLE settings ADD COLUMN llf_prefix VARCHAR(10) DEFAULT 'LLF'"))
                print("[+] Added missing column: settings.llf_prefix")
            conn.commit()
            conn.close()

        # Migration: create vendor_types table if missing
        if "vendor_types" not in inspector.get_table_names():
            conn = engine.connect()
            conn.execute(text("""
                CREATE TABLE vendor_types (
                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(100) NOT NULL UNIQUE,
                    description VARCHAR(255),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
            conn.close()
            print("[+] Created table: vendor_types")

        # Migration: add vendor_type_id to vendors if missing
        vendor_columns = [c["name"] for c in inspector.get_columns("vendors")]
        if "vendor_type_id" not in vendor_columns:
            conn = engine.connect()
            conn.execute(text("ALTER TABLE vendors ADD COLUMN vendor_type_id INTEGER REFERENCES vendor_types(id)"))
            conn.commit()
            conn.close()
            print("[+] Added missing column: vendors.vendor_type_id")

        # Check if we need to seed data
        from app.core.database import SessionLocal
        from app.models import User
        
        db = SessionLocal()
        existing_users = db.query(User).count()
        db.close()
        
        if existing_users == 0:
            print("[+] Database is empty. Seeding initial data...")
            result = subprocess.run(
                [sys.executable, "seed_data.py"],
                capture_output=True,
                text=True,
                cwd=str(Path(__file__).parent)
            )
            if result.returncode == 0:
                print("[+] Seed data loaded successfully")
            else:
                print(f"[!] Warning: Could not seed data - {result.stderr}")
        else:
            print(f"[+] Database already contains {existing_users} users. Skipping seed.")
        
        return True
    except Exception as e:
        print(f"[-] Database setup failed: {e}")
        return False


def run_tests():
    """Run all tests to verify implementation"""
    print("\n" + "="*60)
    print("[TEST] Running tests...")
    print("="*60)
    
    test_files = [
        "tests/test_phase1.py",
        "tests/test_phase2.py",
        "tests/test_phase3.py",
        "tests/test_phase7.py"
    ]
    
    for test_file in test_files:
        test_path = Path(__file__).parent / test_file
        if test_path.exists():
            print(f"\n[>>] Running {test_file}...")
            result = subprocess.run(
                [sys.executable, "-m", "pytest", test_file, "-v", "--tb=short"],
                cwd=str(Path(__file__).parent)
            )
            if result.returncode != 0:
                print(f"[!] Tests failed in {test_file}")
        else:
            print(f"[!] Test file not found: {test_file}")


def start_server():
    """Start FastAPI development server"""
    print("\n" + "="*60)
    print("[*] Starting Cloud9 ERP server...")
    print("="*60)
    
    db_url = os.getenv("DATABASE_URL", "sqlite:///./erp_local.db")
    print(f"\n[DB] Database: {db_url}")
    print("[SERVER] API Server: http://localhost:8000")
    print("[DOCS] API Docs: http://localhost:8000/docs")
    print("[DOCS] ReDoc: http://localhost:8000/redoc")
    
    print("\n" + "="*60)
    print("System Status:")
    print("="*60)
    
    try:
        from app.core.database import SessionLocal
        from app.models import User, Vendor, Order
        
        db = SessionLocal()
        user_count = db.query(User).count()
        vendor_count = db.query(Vendor).count()
        order_count = db.query(Order).count()
        db.close()
        
        print(f"[+] Users: {user_count}")
        print(f"[+] Vendors: {vendor_count}")
        print(f"[+] Orders: {order_count}")
    except Exception as e:
        print(f"[!] Could not load system status: {e}")
    
    print("\n" + "="*60)
    print("Press Ctrl+C to stop the server")
    print("="*60 + "\n")
    
    # Start server
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000",
            "--reload",
            "--reload-exclude", "*.log"
        ])
    except KeyboardInterrupt:
        print("\n\n[*] Server stopped by user")
    except Exception as e:
        print(f"\n[-] Server error: {e}")


if __name__ == "__main__":
    print("\n" + "Cloud9 ERP - Complete System Setup".center(60))
    print("="*60)
    print("Phases: 1-Authentication & RBAC")
    print("        2-Orders & Approvals")
    print("        3-Documents & PDFs")
    print("        4-Vendor Portal")
    print("        5-Email Automation")
    print("        6-Analytics & Reports")
    print("        7-Advanced Features & Polish")
    print("="*60)
    
    # Step 1: Setup database
    if not setup_database():
        sys.exit(1)
    
    # Step 2: Optionally run tests
    if "--test" in sys.argv:
        run_tests()
    
    # Step 3: Start server
    start_server()
