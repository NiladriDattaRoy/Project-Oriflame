import sys
import os
sys.path.append(os.getcwd())
from app import app
from models import db, Product

with app.app_context():
    search = "Giordani Gold Iconic Lip Elixir"
    products = Product.query.filter(Product.name.ilike(f"{search}%")).all()
    print(f"Found {len(products)} products starting with '{search}':")
    for p in products:
        print(f"- ID: {p.id}, Code: {p.code}, Name: {p.name}, Shade: {p.shade_name}, Parent: {p.parent_id}, Active: {p.is_active}")
    
    search2 = "The ONE Smart Sync Lipstick"
    products2 = Product.query.filter(Product.name.ilike(f"{search2}%")).all()
    print(f"\nFound {len(products2)} products starting with '{search2}':")
    for p in products2:
        print(f"- ID: {p.id}, Code: {p.code}, Name: {p.name}, Shade: {p.shade_name}, Parent: {p.parent_id}, Active: {p.is_active}")
