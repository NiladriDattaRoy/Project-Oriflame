
from app import app, db, Product

with app.app_context():
    p = Product.query.get(102)
    print(f"Product: {p.name}")
    print(f"Parent ID: {p.parent_id}")
    print(f"Code: {p.code}")
    print(f"Color 1: {p.shade_color}")
    print(f"Color 2: {p.shade_color_2}")
    
    variants = Product.query.filter_by(parent_id=102).all()
    print(f"\nVariants ({len(variants)}):")
    for v in variants:
        print(f" - {v.shade_name} ({v.code}): {v.shade_color} / {v.shade_color_2}")
