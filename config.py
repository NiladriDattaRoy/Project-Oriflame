"""
Configuration settings for the Oriflame E-Commerce & MLM Platform.
"""
import os
from dotenv import load_dotenv

load_dotenv(override=True)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'oriflame-secret-key-x9k2-2026')
    db_url = os.environ.get('DATABASE_URL')
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    
    SQLALCHEMY_DATABASE_URI = db_url or f'sqlite:///{os.path.join(BASE_DIR, "database", "oriflame.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Connection pooling for cloud DBs (Aiven/Neon)
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 3600,
        "pool_pre_ping": True,
        "pool_size": 10,
        "max_overflow": 20,
    }

    # Upload settings
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'images', 'uploads')

    # Razorpay Settings
    RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', '')
    RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', '')

    # Admin settings
    ADMIN_URL_PREFIX = '/oriflame-admin-panel-x9k2'
    ADMIN_EMAIL = 'admin@oriflame.com'
    ADMIN_DEFAULT_PASSWORD = 'admin123'

    # MLM Commission rates (percentage)
    MLM_COMMISSION_RATES = {
        1: 10.0,  # Level 1: Direct sponsor gets 10%
        2: 5.0,   # Level 2: Sponsor's sponsor gets 5%
        3: 2.0,   # Level 3: 3rd level gets 2%
    }

    # Pagination
    PRODUCTS_PER_PAGE = 12
    ORDERS_PER_PAGE = 10
