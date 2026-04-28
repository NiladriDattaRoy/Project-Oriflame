import sys
from sqlalchemy import create_engine, text

def generate_preview(cloud_url):
    print("🌐 Connecting to Aiven Cloud...")
    if cloud_url.startswith("postgres://"):
        cloud_url = cloud_url.replace("postgres://", "postgresql://", 1)
        
    try:
        engine = create_engine(cloud_url)
        with engine.connect() as conn:
            print("📦 Fetching products...")
            result = conn.execute(text("SELECT id, name, price, category_id, code FROM products ORDER BY id ASC"))
            products = result.fetchall()
            
            # Generate HTML
            html = """
            <html>
            <head>
                <title>Cloud Products Preview</title>
                <style>
                    body { font-family: sans-serif; padding: 40px; background: #f4f7f6; }
                    h1 { color: #333; }
                    table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
                    th, td { padding: 15px; text-align: left; border-bottom: 1px solid #eee; }
                    th { background: #007bff; color: white; }
                    tr:hover { background: #f9f9f9; }
                    .status { color: green; font-weight: bold; margin-bottom: 20px; border: 1px solid green; padding: 10px; border-radius: 5px; background: #e8f5e9; display: inline-block; }
                </style>
            </head>
            <body>
                <h1>Aiven Cloud Data Inspector</h1>
                <div class="status">✓ Successfully connected to pg-8d841bd-niladridattaroy25-b077.a.aivencloud.com</div>
                <p>Showing <strong>{count}</strong> products found in the cloud database.</p>
                <table>
                    <tr><th>ID</th><th>Item Code</th><th>Product Name</th><th>Price</th><th>Category ID</th></tr>
            """.replace("{count}", str(len(products)))
            
            for p in products:
                html += f"<tr><td>{p[0]}</td><td>{p[4]}</td><td>{p[1]}</td><td>₹{p[2]}</td><td>{p[3]}</td></tr>"
                
            html += "</table></body></html>"
            
            with open("cloud_products_preview.html", "w", encoding="utf-8") as f:
                f.write(html)
                
            print("\n✅ SUCCESS: Preview file created!")
            print("👉 Open 'cloud_products_preview.html' in your browser to see your data.")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python view_products.py 'your_aiven_uri'")
    else:
        generate_preview(sys.argv[1])
