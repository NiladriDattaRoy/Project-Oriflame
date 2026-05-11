import sys
sys.path.insert(0, '.')
from app import app
from models import Category, Product

with app.app_context():
    cats = Category.query.all()
    print(f"Total categories: {len(cats)}")
    for c in cats:
        active = getattr(c, 'is_active', 'N/A')
        print(f"ID: {c.id}, Name: {c.name}, Slug: {c.slug}, is_active: {active}")
    
    print()
    # Check makeup category specifically
    makeup = Category.query.filter_by(slug='makeup').first()
    if makeup:
        print(f"Makeup category found: ID={makeup.id}, active={getattr(makeup, 'is_active', 'N/A')}")
        prods = Product.query.filter_by(category_id=makeup.id, is_active=True).count()
        print(f"Active products in makeup: {prods}")
    else:
        print("Makeup category NOT found in local DB")
