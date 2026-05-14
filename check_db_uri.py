
from app import app
print(f"DB URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
