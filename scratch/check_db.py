import sys
import os

# Add the current directory to sys.path
sys.path.append(os.getcwd())

from app import app
from models import db, Product

with app.app_context():
    products = Product.query.all()
    print(f"Total products: {len(products)}")
    for p in products:
        if p.name is None:
            print(f"ERROR: Product {p.id} has no name!")
        if p.slug is None:
            print(f"ERROR: Product {p.id} ({p.name}) has no slug!")
    print("Done checking.")
