import sqlite3

# Path to your SQLite database file
DB_PATH = 'loyalty.db'

# List of problematic indexes and tables to drop
indexes = [
    'ix_menu_items_restaurant_id',
    'menu_items_restaurant_id',
]
tables = [
    'menu_items_old',
    'menu_categories_new',
]

def cleanup():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for idx in indexes:
        try:
            print(f"Dropping index {idx} if exists...")
            c.execute(f'DROP INDEX IF EXISTS {idx}')
        except Exception as e:
            print(f"Error dropping index {idx}: {e}")
    for tbl in tables:
        try:
            print(f"Dropping table {tbl} if exists...")
            c.execute(f'DROP TABLE IF EXISTS {tbl}')
        except Exception as e:
            print(f"Error dropping table {tbl}: {e}")
    conn.commit()
    conn.close()
    print("Cleanup complete.")

if __name__ == '__main__':
    cleanup()
