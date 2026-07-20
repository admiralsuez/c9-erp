import sqlite3

conn = sqlite3.connect('./erp_local.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(inventory_items)")
columns = cursor.fetchall()

print("Current inventory_items columns:")
for col in columns:
    print(f"  {col[1]}: {col[2]}")

# Check if is_container exists
has_is_container = any(col[1] == 'is_container' for col in columns)
print(f"\nis_container column exists: {has_is_container}")

conn.close()
