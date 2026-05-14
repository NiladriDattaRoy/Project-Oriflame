
from app import app, db, Product

with app.app_context():
    # 1. Check for missing images
    no_image = Product.query.filter((Product.image_url == None) | (Product.image_url == '') | (Product.image_url.like('%placeholder%'))).all()
    print(f"Products with missing/placeholder images: {len(no_image)}")
    for p in no_image[:10]:
        print(f" - {p.name} (ID: {p.id}, Code: {p.code})")

    # 2. Check for duplicates (same name and code)
    from sqlalchemy import func
    duplicates = db.session.query(Product.name, Product.code, func.count('*')).group_by(Product.name, Product.code).having(func.count('*') > 1).all()
    print(f"\nDuplicate Name+Code combinations: {len(duplicates)}")
    for name, code, count in duplicates:
        print(f" - {name} ({code}): {count} occurrences")

    # 3. Check for duplicates (same name but different code - might be unintentional)
    duplicates_name = db.session.query(Product.name, func.count('*')).group_by(Product.name).having(func.count('*') > 1).all()
    print(f"\nDuplicate Name occurrences: {len(duplicates_name)}")
    for name, count in duplicates_name:
        # Check if they are already linked via parent_id
        count_orphans = Product.query.filter_by(name=name, parent_id=None).count()
        print(f" - {name}: {count} total, {count_orphans} orphans")
