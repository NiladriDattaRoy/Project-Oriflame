
import sys
import os
sys.path.append(os.getcwd())
from app import app, db, Product

with app.app_context():
    all_p = Product.query.filter(Product.code.ilike('%46590%')).all()
    for p in all_p:
        print(f"ID: {p.id}, Name: {p.name}, Code: {p.code}")
