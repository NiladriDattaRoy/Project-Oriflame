import psycopg2
import sys

def check_columns(db_url):
    print(f"Connecting to: {db_url[:20]}...")
    try:
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
            
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='products'")
        columns = [row[0] for row in cur.fetchall()]
        
        print("\nColumns currently in 'products' table:")
        print("-" * 30)
        for col in sorted(columns):
            print(f"  - {col}")
        print("-" * 30)
        
        missing = []
        if 'parent_id' not in columns: missing.append('parent_id')
        if 'shade_color_2' not in columns: missing.append('shade_color_2')
        
        if not missing:
            print("\n✅ SUCCESS: All required columns are present!")
        else:
            print(f"\n❌ MISSING COLUMNS: {', '.join(missing)}")
            print("\nRun these commands to fix it:")
            if 'parent_id' in missing:
                print("ALTER TABLE products ADD COLUMN parent_id INTEGER REFERENCES products(id);")
            if 'shade_color_2' in missing:
                print("ALTER TABLE products ADD COLUMN shade_color_2 VARCHAR(20);")
                
        cur.close()
        conn.close()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_db.py 'your_db_url'")
    else:
        check_columns(sys.argv[1])
