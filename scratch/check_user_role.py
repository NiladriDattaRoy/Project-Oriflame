from app import app
from models import User

with app.app_context():
    user = User.query.filter_by(email='niladridattaroy25@gmail.com').first()
    if user:
        print(f"User: {user.email}")
        print(f"Role: {user.role}")
        print(f"Is Admin: {user.is_admin}")
    else:
        print("User not found.")
