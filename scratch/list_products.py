import sys
import os
sys.path.append(os.getcwd())

from app import app, db, Product

with app.app_context():
    products = Product.query.filter(Product.name.ilike('%Eyeshadow%')).all()
    print(f"Found {len(products)} products.")
    for p in products:
        print(f"ID: {p.id}, Code: {p.code}, Name: {p.name}")
