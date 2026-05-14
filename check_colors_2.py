
from app import app, db, Product

with app.app_context():
    # Find products where shade_color_2 is exactly '#000000'
    # This might have been set by the bug where it defaults to black
    products = Product.query.filter(Product.shade_color_2 == '#000000').all()
    print(f"Products with shade_color_2 == '#000000': {len(products)}")
    for p in products:
        print(f"ID: {p.id}, Name: {p.name}, Code: {p.code}")
    
    # Also find products where shade_color_2 is empty string
    empty_products = Product.query.filter(Product.shade_color_2 == '').all()
    print(f"\nProducts with shade_color_2 == '': {len(empty_products)}")
    for p in empty_products:
        print(f"ID: {p.id}, Name: {p.name}, Code: {p.code}")

    # I'll also clear them to None
    count = 0
    for p in products:
        p.shade_color_2 = None
        count += 1
    for p in empty_products:
        p.shade_color_2 = None
        count += 1
    
    db.session.commit()
    print(f"\nCleared {count} products to shade_color_2 = None")
