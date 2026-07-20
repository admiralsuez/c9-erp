import sqlite3

conn = sqlite3.connect('./erp_local.db')
cursor = conn.cursor()

# Check if is_container column already exists
cursor.execute("PRAGMA table_info(inventory_items)")
columns = {col[1] for col in cursor.fetchall()}

if 'is_container' not in columns:
    print("Adding is_container column...")
    cursor.execute("""
        ALTER TABLE inventory_items 
        ADD COLUMN is_container BOOLEAN DEFAULT 0 NOT NULL
    """)
    print("✓ is_container column added")
else:
    print("✓ is_container column already exists")

# Check if inventory_item_attributes table exists
cursor.execute("""
    SELECT name FROM sqlite_master 
    WHERE type='table' AND name='inventory_item_attributes'
""")
if not cursor.fetchone():
    print("Creating inventory_item_attributes table...")
    cursor.execute("""
        CREATE TABLE inventory_item_attributes (
            id INTEGER PRIMARY KEY,
            item_id INTEGER NOT NULL,
            attribute_name VARCHAR(100) NOT NULL,
            attribute_value TEXT NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(item_id) REFERENCES inventory_items(id) ON DELETE CASCADE,
            UNIQUE(item_id, attribute_name)
        )
    """)
    cursor.execute("""
        CREATE INDEX idx_item_attr_name ON inventory_item_attributes(attribute_name)
    """)
    print("✓ inventory_item_attributes table created")
else:
    print("✓ inventory_item_attributes table already exists")

conn.commit()
conn.close()
print("\nMigration complete!")
