from app import app
from models import db, User

with app.app_context():
    user = User.query.filter_by(email='niladridattaroy25@gmail.com').first()
    if user:
        user.role = 'admin'
        db.session.commit()
        print(f"User {user.email} promoted to admin.")
    else:
        print("User not found.")
