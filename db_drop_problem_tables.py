import sqlite3

DB_PATH = 'loyalty.db'
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# List all tables for visibility
c.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = c.fetchall()
print("Tables:", tables)

# Drop problematic tables
for tbl in ['menu_items_old', 'menu_items_new', 'menu_categories_new']:
    print(f"Dropping table {tbl} if exists...")
    c.execute(f"DROP TABLE IF EXISTS {tbl}")

conn.commit()
conn.close()
print("Problem tables dropped.")
