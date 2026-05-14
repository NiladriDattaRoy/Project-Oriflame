
import sys
import os
sys.path.append(os.getcwd())
from app import app, db, Product, ProductImage, parse_media_url

with app.app_context():
    # Find the specific product
    p = Product.query.filter_by(code='46590').first()
    if not p:
        print("Product 46590 not found.")
    else:
        print(f"Checking product: {p.name} ({p.code})")
        images = ProductImage.query.filter_by(product_id=p.id).all()
        for img in images:
            # Re-parse the URL
            url, m_type = parse_media_url(img.image_url)
            if m_type == 'video' and img.media_type != 'video':
                print(f"Updating media {img.id} from image to video: {img.image_url}")
                img.media_type = 'video'
        
        db.session.commit()
        print("Update complete.")
