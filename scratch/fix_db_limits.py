
import os
import sys
# Add parent directory to path to import app and db
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from sqlalchemy import text

def fix_limits():
    with app.app_context():
        print(f"Connected to: {app.config['SQLALCHEMY_DATABASE_URI']}")
        
        commands = [
            # Product table
            "ALTER TABLE products ALTER COLUMN name TYPE VARCHAR(512)",
            "ALTER TABLE products ALTER COLUMN code TYPE VARCHAR(100)",
            "ALTER TABLE products ALTER COLUMN slug TYPE VARCHAR(512)",
            "ALTER TABLE products ALTER COLUMN short_description TYPE VARCHAR(2000)",
            "ALTER TABLE products ALTER COLUMN weight TYPE VARCHAR(100)",
            "ALTER TABLE products ALTER COLUMN image_url TYPE VARCHAR(1024)",
            "ALTER TABLE products ALTER COLUMN image_url_2 TYPE VARCHAR(1024)",
            
            # Category table
            "ALTER TABLE categories ALTER COLUMN name TYPE VARCHAR(512)",
            "ALTER TABLE categories ALTER COLUMN slug TYPE VARCHAR(512)",
            "ALTER TABLE categories ALTER COLUMN image_url TYPE VARCHAR(1024)",
            
            # ProductImage table
            "ALTER TABLE product_images ALTER COLUMN image_url TYPE VARCHAR(1024)"
        ]
        
        # If SQLite, these commands might fail or be unnecessary as SQLite doesn't enforce VARCHAR limits
        is_sqlite = app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite')
        
        for cmd in commands:
            try:
                print(f"Executing: {cmd}")
                db.session.execute(text(cmd))
                print("Success.")
            except Exception as e:
                if is_sqlite:
                    print(f"Skipping for SQLite (likely unsupported): {e}")
                else:
                    print(f"Error: {e}")
        
        db.session.commit()
        print("All migrations completed.")

if __name__ == "__main__":
    fix_limits()
