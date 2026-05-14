
from app import app, db, Product

with app.app_context():
    name = "The ONE Colour Stylist Super Pout Lipstick"
    products = Product.query.filter(Product.name == name).all()
    print(f"Products with name '{name}':")
    for p in products:
        print(f"ID: {p.id}, Code: {p.code}, Parent: {p.parent_id}")
