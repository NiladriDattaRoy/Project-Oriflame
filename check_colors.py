
from app import app, db, Product

with app.app_context():
    # Find products where shade_color_2 is set but might be just a default
    products = Product.query.filter(Product.shade_color_2.isnot(None)).all()
    print(f"Total products with shade_color_2: {len(products)}")
    for p in products:
        print(f"ID: {p.id}, Name: {p.name}, Code: {p.code}, Color 1: {p.shade_color}, Color 2: {p.shade_color_2}")
