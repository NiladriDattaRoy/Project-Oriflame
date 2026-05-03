import sys
import os
sys.path.append(os.getcwd())

from app import app, db, Product

with app.app_context():
    # Search by name and code
    products = Product.query.filter(Product.name.ilike('%Unlimited Eye Shadow%')).all()
    print(f"Found {len(products)} products with 'Unlimited Eye Shadow' in name.")
    for p in products:
        print(f"ID: {p.id}, Code: {repr(p.code)}, Name: {p.name}")
