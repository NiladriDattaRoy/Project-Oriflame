from app import app, db
from models import Product, User

with app.app_context():
    product = Product.query.first()
    if product:
        print(f"Product ID: {product.id}, Name: {product.name}")
    else:
        print("No products found")
