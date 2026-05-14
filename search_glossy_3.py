
from app import app, db, Product

with app.app_context():
    products = Product.query.filter(Product.name.like("%Glossy%")).all()
    print(f"Found {len(products)} products")
    for p in products:
        print(f"ID: {p.id}, Name: {p.name}, Code: {p.code}, Shade: {p.shade_name}, C1: {p.shade_color}, C2: {p.shade_color_2}")
