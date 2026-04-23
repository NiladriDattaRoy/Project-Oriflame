from app import app, db
from models import Product, Category

with app.app_context():
    prod = Product.query.filter(Product.name.ilike('%Giordani Gold Age Defying Serum Boost Foundation%')).first()
    cat = Category.query.filter(Category.name.ilike('%Makeup%')).first()
    
    if prod and cat:
        print(f"Found product: {prod.name}")
        if prod.category:
            print(f"Current category: {prod.category.name}")
        print(f"Found target category: {cat.name}")
        
        prod.category_id = cat.id
        db.session.commit()
        print("Updated successfully.")
    else:
        print("Failed:")
        if not prod: print("- Product not found")
        if not cat: print("- Category not found")
