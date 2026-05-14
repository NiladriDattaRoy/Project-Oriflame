from app import app
from models import User

with app.app_context():
    admins = User.query.filter_by(role='admin').all()
    print(f"Total Admins: {len(admins)}")
    for a in admins:
        print(f"Admin: {a.email}")
