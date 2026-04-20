"""
Configuration settings for the Oriflame E-Commerce & MLM Platform.
"""
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'oriflame-secret-key-x9k2-2026')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f'sqlite:///{os.path.join(BASE_DIR, "database", "oriflame.db")}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Upload settings
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'images', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload

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

    # Razorpay (https://razorpay.com/) — UPI, cards, netbanking via hosted Checkout.
    # Test keys: Dashboard → Settings → API Keys → Generate test key.
    # Set both in production; never commit the secret. Amounts are in INR on orders; Razorpay uses paise.
    RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', '').strip()
    RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', '').strip()
    RAZORPAY_ENABLED = bool(RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET)
