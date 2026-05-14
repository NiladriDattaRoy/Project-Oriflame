
from app import app, db, Product

with app.app_context():
    p = Product.query.filter_by(code='46590').first()
    if p:
        print(f"Product: {p.name}")
        print(f"Shade Name: {p.shade_name}")
        print(f"Color 1: '{p.shade_color}'")
        print(f"Color 2: '{p.shade_color_2}'")
        print(f"Color 2 type: {type(p.shade_color_2)}")
    else:
        print("Product 46590 not found.")
