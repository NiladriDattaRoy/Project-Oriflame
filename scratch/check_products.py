from app import app, Product
with app.app_context():
    products = Product.query.filter(Product.name.like('The ONE%')).all()
    print(f"Found {len(products)} The ONE products")
    for p in products:
        print(f"ID: {p.id} | Name: {p.name} | Parent: {p.parent_id}")
