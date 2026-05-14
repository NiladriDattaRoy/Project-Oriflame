from app import app
from models import Product, ProductImage

slug = "oncolour-oncolour-oh-sweet-glossy"

with app.app_context():
    product = Product.query.filter_by(slug=slug).first()
    if product:
        print(f"Product: {product.name} (ID: {product.id})")
        print(f"Main Image: {product.image_url}")
        print("\nGallery Images:")
        for img in product.images.all():
            print(f"- URL: {img.image_url} | Type: {img.media_type}")
    else:
        print("Product not found.")
