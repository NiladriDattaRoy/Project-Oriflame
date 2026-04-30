from app import app, db
from models import Product

with app.app_context():
    # Clean up first
    Product.query.filter_by(code='test-main').delete()
    Product.query.filter_by(code='test-var1').delete()
    db.session.commit()

    # Create main product
    main_p = Product(name='Test Lipstick', code='test-main', price=10, mrp=15, is_active=True, slug='test-lipstick')
    db.session.add(main_p)
    db.session.flush()

    # Emulate inline variants logic
    v_codes = ['test-var1']
    v_names = ['Red']
    v_colors = ['#ff0000']
    
    for i in range(len(v_codes)):
        code = v_codes[i]
        variant = Product(code=code)
        db.session.add(variant)
        
        variant.parent_id = main_p.id
        variant.name = main_p.name
        variant.slug = f"test-lipstick-{code}"
        variant.shade_name = v_names[i]
        variant.shade_color = v_colors[i]
        variant.is_active = True
        variant.price = main_p.price
        variant.mrp = main_p.mrp

    db.session.commit()

    # Query variants for main product
    root_id = main_p.parent_id if main_p.parent_id else main_p.id
    from sqlalchemy import or_
    variants = Product.query.filter(
        or_(Product.id == root_id, Product.parent_id == root_id),
        Product.id != main_p.id,
        Product.is_active == True
    ).all()

    print("Main product ID:", main_p.id)
    print("Variants found:", [(v.id, v.code, v.parent_id) for v in variants])
