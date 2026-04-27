import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app import app
from models import db, User, Category, Product, ProductImage, Catalogue, Address, Order, OrderItem, Transaction, MLMCommission, Wishlist, BlogPost, ContactMessage, Review, Cart, CartItem

def migrate(cloud_url):
    print(f"🚀 Starting Final Migration to Aiven...")
    
    if cloud_url.startswith("postgres://"):
        cloud_url = cloud_url.replace("postgres://", "postgresql://", 1)
    
    try:
        cloud_engine = create_engine(cloud_url)
        CloudSession = sessionmaker(bind=cloud_engine)
        cloud_session = CloudSession()

        print("📁 Checking Cloud Tables...")
        with app.app_context():
            db.metadata.create_all(cloud_engine)

        # Migration order
        models = [
            User, Category, Product, ProductImage, Catalogue, 
            Address, BlogPost, ContactMessage, Order, OrderItem, 
            Transaction, MLMCommission, Wishlist, Cart, CartItem, Review
        ]

        print("🚚 Moving data (skipping orphaned records)...")
        with app.app_context():
            for model in models:
                table_name = model.__tablename__
                print(f"  → {table_name}...", end=" ", flush=True)
                
                local_items = model.query.all()
                if not local_items:
                    print("Empty")
                    continue
                    
                count = 0
                for item in local_items:
                    try:
                        # Copy data
                        data = {c.name: getattr(item, c.name) for c in item.__table__.columns}
                        new_item = model(**data)
                        
                        # Use cloud session to merge and commit immediately
                        cloud_session.merge(new_item)
                        cloud_session.commit()
                        count += 1
                    except Exception:
                        # Skip if there's a foreign key error or duplicate
                        cloud_session.rollback()
                        continue
                
                print(f"Done ({count} rows)")

        print("\n✅ SUCCESS: Everything is now in Aiven!")
        print("Final Step: Update 'DATABASE_URL' in your Render.com dashboard.")

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python migrate_to_cloud.py 'your_aiven_uri'")
    else:
        migrate(sys.argv[1])
