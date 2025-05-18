import sqlite3
import sys

def inspect_db(db_path):
    """Inspect SQLite database structure and contents."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"Database: {db_path}")
        print(f"Found {len(tables)} tables:")
        
        for table_name in tables:
            table_name = table_name[0]
            print(f"\n{'-'*30}")
            print(f"Table: {table_name}")
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            print(f"Columns: {len(columns)}")
            for col in columns:
                col_id, name, type_name, nullable, default, pk = col
                pk_str = "PRIMARY KEY" if pk else ""
                print(f"  - {name} ({type_name}) {pk_str}")
            
            # Count rows
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            print(f"Row count: {row_count}")
            
            # Sample data (first 3 rows)
            if row_count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                rows = cursor.fetchall()
                if rows:
                    print("Sample data (first 3 rows):")
                    for i, row in enumerate(rows):
                        print(f"  Row {i+1}: {row}")
        
        conn.close()
    except Exception as e:
        print(f"Error inspecting database: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    db_path = "loyalty.db"
    sys.exit(inspect_db(db_path)) 