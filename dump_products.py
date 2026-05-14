
from app import app, db, Product

with app.app_context():
    all_products = Product.query.all()
    with open('all_products.txt', 'w', encoding='utf-8') as f:
        for p in all_products:
            f.write(f"ID: {p.id}, Code: {p.code}, Name: {p.name}, Shade: {p.shade_name}, C1: {p.shade_color}, C2: {p.shade_color_2}\n")
    print(f"Total products: {len(all_products)}")
