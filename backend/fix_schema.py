"""
One-time script to add missing columns to the users table.
Run from the backend directory:  python fix_schema.py
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "erp_local.db")
print(f"[i] Database: {DB_PATH}")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# ── Show existing columns ──────────────────────────────────────────────────────
cur.execute("PRAGMA table_info(users)")
existing_cols = {row[1] for row in cur.fetchall()}
print("\nExisting columns:", sorted(existing_cols))

# ── Columns the model expects and their SQL definition ────────────────────────
wanted = {
    "department" : "TEXT",
    "location"   : "TEXT DEFAULT 'HO'",
}

for col, typedef in wanted.items():
    if col not in existing_cols:
        sql = f"ALTER TABLE users ADD COLUMN {col} {typedef}"
        print(f"[+] {sql}")
        cur.execute(sql)
    else:
        print(f"[~] Column already exists: {col}")

conn.commit()
conn.close()
print("\n[✓] Schema fix complete. Restart uvicorn if it is running.")
