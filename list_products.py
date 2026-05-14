
from app import app, db, Product

with app.app_context():
    all_products = Product.query.all()
    print(f"Total products: {len(all_products)}")
    for p in all_products[:20]: # Show first 20
        print(f"ID: {p.id}, Name: {p.name}")
