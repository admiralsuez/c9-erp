"""
Seed script to create an admin user in the SQLite database.

Run from the backend directory:
    python seed_admin.py

Uses raw sqlite3 so it is immune to ORM model/migration drift.
"""
import sys
import os
import sqlite3
import re
from dotenv import load_dotenv

# Load .env so DATABASE_URL is available
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# ── CONFIG ────────────────────────────────────────────────────────────────────
ADMIN_EMAIL    = "admin@example.com"
ADMIN_PASSWORD = "admin@123"
ADMIN_NAME     = "Admin User"
ADMIN_ROLE     = "Admin"
# ─────────────────────────────────────────────────────────────────────────────

# Resolve the DB file path from DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL", "")
if not DATABASE_URL:
    raise SystemExit("[!] DATABASE_URL not set in .env")

if not DATABASE_URL.startswith("sqlite"):
    raise SystemExit("[!] This script only supports SQLite. Use a proper migration tool for PostgreSQL.")

# Strip the sqlite:/// prefix (handles both absolute and relative paths)
db_path = re.sub(r"^sqlite:///", "", DATABASE_URL)
if not os.path.isabs(db_path):
    db_path = os.path.join(os.path.dirname(__file__), db_path)

print(f"[i] Using database: {db_path}")

# ── Hash password via bcrypt (same as auth.py) ────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))
from app.core.auth import hash_password


def get_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    """Return list of column names for a table."""
    cur = conn.execute(f"PRAGMA table_info({table})")
    return [row[1] for row in cur.fetchall()]


def seed():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    try:
        # ── 1. Ensure Admin role exists ──────────────────────────────────────
        cur.execute("SELECT id FROM roles WHERE name = ?", (ADMIN_ROLE,))
        role_row = cur.fetchone()
        if role_row:
            role_id = role_row["id"]
            print(f"[~] Role already exists: {ADMIN_ROLE} (id={role_id})")
        else:
            cur.execute(
                "INSERT INTO roles (name, description) VALUES (?, ?)",
                (ADMIN_ROLE, "Super administrator with full access"),
            )
            role_id = cur.lastrowid
            print(f"[+] Created role: {ADMIN_ROLE} (id={role_id})")

        # ── 2. Check if user already exists ─────────────────────────────────
        user_cols = get_columns(conn, "users")
        cur.execute("SELECT id, email FROM users WHERE email = ?", (ADMIN_EMAIL,))
        existing = cur.fetchone()
        if existing:
            print(f"[~] User already exists: {existing['email']} (id={existing['id']})")
            print("    Nothing to do — log in with the existing credentials.")
            return

        # ── 3. Insert user with only the columns that exist in the DB ────────
        password_hash = hash_password(ADMIN_PASSWORD)

        candidate = {
            "full_name"     : ADMIN_NAME,
            "email"         : ADMIN_EMAIL,
            "password_hash" : password_hash,
            "role_id"       : role_id,
            "is_active"     : 1,
        }
        # Add optional columns only if they exist in the actual table
        optional = {
            "location"   : "HO",
            "department" : None,
        }
        for col, val in optional.items():
            if col in user_cols and val is not None:
                candidate[col] = val

        cols_sql = ", ".join(candidate.keys())
        placeholders = ", ".join(["?"] * len(candidate))
        values = list(candidate.values())

        cur.execute(
            f"INSERT INTO users ({cols_sql}) VALUES ({placeholders})",
            values,
        )
        new_id = cur.lastrowid
        conn.commit()

        print(f"[+] Admin user created successfully!")
        print(f"    id       : {new_id}")
        print(f"    email    : {ADMIN_EMAIL}")
        print(f"    password : {ADMIN_PASSWORD}")
        print(f"    role     : {ADMIN_ROLE}")

    except sqlite3.IntegrityError as e:
        conn.rollback()
        print(f"[!] IntegrityError: {e}")
    except Exception as e:
        conn.rollback()
        print(f"[!] Unexpected error: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    seed()

