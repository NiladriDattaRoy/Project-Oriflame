import sys
from sqlalchemy import create_engine, inspect, text

def inspect_cloud(cloud_url):
    print(f"🔍 Inspecting your Aiven Cloud Database...\n")
    
    if cloud_url.startswith("postgres://"):
        cloud_url = cloud_url.replace("postgres://", "postgresql://", 1)
        
    try:
        engine = create_engine(cloud_url)
        inspector = inspect(engine)
        
        with engine.connect() as conn:
            tables = inspector.get_table_names()
            
            print(f"{'Table Name':<20} | {'Total Rows':<10}")
            print("-" * 35)
            
            for table in sorted(tables):
                # Count rows in each table
                try:
                    result = conn.execute(text(f'SELECT COUNT(*) FROM "{table}"'))
                    count = result.scalar()
                    print(f"{table:<20} | {count:<10}")
                except:
                    continue
                
            print("\n✅ If you see numbers above 0, your data is safely in the cloud!")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python inspect_cloud.py 'your_aiven_uri'")
    else:
        inspect_cloud(sys.argv[1])
