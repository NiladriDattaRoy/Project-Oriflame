from app import app, db
from models import Product

with app.app_context():
    products = Product.query.filter(Product.name.ilike('%ultra fix lipstick%')).all()
    print(f"Found {len(products)} products matching 'ultra fix lipstick'")
    for p in products:
        print(f"ID: {p.id}, Name: {p.name}, Slug: {p.slug}, Parent ID: {p.parent_id}, Shade Name: {p.shade_name}")
