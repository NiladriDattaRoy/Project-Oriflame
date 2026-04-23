import sqlite3
import os

# Get the project root (one level up from scratch)
SCRATCH_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.dirname(SCRATCH_DIR)
db_path = os.path.join(PROJECT_ROOT, 'database', 'oriflame.db')

print(f"Connecting to database at: {db_path}")

if not os.path.exists(db_path):
    print(f"Error: Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Add media_type column
    cursor.execute("ALTER TABLE product_images ADD COLUMN media_type VARCHAR(20) DEFAULT 'image'")
    conn.commit()
    print("Success: Added media_type column to product_images table.")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e).lower():
        print("Column media_type already exists.")
    else:
        print(f"Error adding media_type: {e}")
except Exception as e:
    print(f"General Error: {e}")
finally:
    conn.close()
