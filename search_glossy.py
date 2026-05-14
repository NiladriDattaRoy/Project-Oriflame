
from app import app, db, Product

with app.app_context():
    name = "OnColour OnColour Oh! Sweet Glossy"
    products = Product.query.filter(Product.name.like(f"%{name}%")).all()
    print(f"Found {len(products)} products matching '{name}'")
    for p in products:
        print(f"ID: {p.id}, Code: {p.code}, Shade: {p.shade_name}, C1: {p.shade_color}, C2: {p.shade_color_2}")
