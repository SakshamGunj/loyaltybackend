import sqlite3

DB_PATH = 'loyalty.db'
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='menu_items';")
indexes = c.fetchall()
for idx in indexes:
    print(f"Dropping index {idx[0]}")
    c.execute(f"DROP INDEX IF EXISTS {idx[0]}")
conn.commit()
conn.close()
print("All indexes on menu_items dropped.")
