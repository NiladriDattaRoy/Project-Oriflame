import sys
import os
sys.path.append(os.getcwd())
from app import app
from models import db, Product

with app.app_context():
    search = "The ONE Colour Stylist Super Pout Lipstick"
    products = Product.query.filter(Product.name.ilike(f"{search}%")).all()
    print(f"Found {len(products)} products starting with '{search}':")
    for p in products:
        print(f"- ID: {p.id}, Code: {p.code}, Name: {p.name}, Shade: {p.shade_name}, Parent: {p.parent_id}, Active: {p.is_active}")
