from app import app
from models import db, User

with app.app_context():
    users = User.query.all()
    for u in users:
        print(f"Email: {u.email}, Role: {u.role}, Is Admin: {u.is_admin}")
