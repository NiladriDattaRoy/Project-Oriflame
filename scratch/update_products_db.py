import sqlite3
import os

# Path to the database
db_path = os.path.join(os.getcwd(), 'database', 'oriflame.db')

def add_columns():
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Adding 'how_to_use' and 'ingredients' columns to 'products' table...")
        
        # Add columns if they don't exist
        try:
            cursor.execute("ALTER TABLE products ADD COLUMN how_to_use TEXT")
        except sqlite3.OperationalError:
            print("how_to_use column already exists.")
            
        try:
            cursor.execute("ALTER TABLE products ADD COLUMN ingredients TEXT")
        except sqlite3.OperationalError:
            print("ingredients column already exists.")
        
        conn.commit()
        conn.close()
        print("Columns updated successfully!")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    add_columns()
