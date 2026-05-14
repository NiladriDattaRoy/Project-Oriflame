
import sys
import os
sys.path.append(os.getcwd())
from app import app, db, Product

with app.app_context():
    p = Product.query.filter(Product.slug.ilike('%46590%')).first()
    if p:
        print(f"ID: {p.id}, Name: {p.name}, Code: {p.code}, Slug: {p.slug}")
    else:
        # Just find any product to see what's in the DB
        first = Product.query.first()
        if first:
            print(f"First product in DB: {first.name}, Code: {first.code}")
        else:
            print("DB is empty!")
