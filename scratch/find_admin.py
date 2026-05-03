import sys
import os
sys.path.append(os.getcwd())
from app import app
from models import db, User

with app.app_context():
    admins = User.query.filter_by(role='admin').all()
    for admin in admins:
        print(f"Admin: {admin.email}")
