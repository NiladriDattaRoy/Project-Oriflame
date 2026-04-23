import sqlite3
import os

SCRATCH_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.dirname(SCRATCH_DIR)
db_path = os.path.join(PROJECT_ROOT, 'database', 'oriflame.db')

print(f"Connecting to database at: {db_path}")

if not os.path.exists(db_path):
    print(f"Error: Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

def add_column(table, column, type_def):
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {type_def}")
        conn.commit()
        print(f"Success: Added {column} to {table}.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print(f"Column {column} already exists in {table}.")
        else:
            print(f"Error adding {column}: {e}")

add_column('products', 'shade_name', 'VARCHAR(100)')
add_column('products', 'shade_color', 'VARCHAR(20)')

conn.close()
