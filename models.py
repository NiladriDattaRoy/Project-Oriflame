"""
Database models for the Oriflame E-Commerce & MLM Platform.
Uses SQLAlchemy ORM with SQLite.
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """User model supporting customers, brand partners, and admins."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(15))
    avatar_url = db.Column(db.String(256))
    role = db.Column(db.String(20), nullable=False, default='customer')  # customer, partner, admin
    sponsor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    join_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    total_sales = db.Column(db.Float, default=0.0)
    total_commission = db.Column(db.Float, default=0.0)

    # Relationships
    sponsor = db.relationship('User', remote_side=[id], backref='downlines')
    addresses = db.relationship('Address', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    cart = db.relationship('Cart', backref='user', uselist=False, cascade='all, delete-orphan')
    wishlist_items = db.relationship('Wishlist', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    commissions = db.relationship('MLMCommission', backref='user', lazy='dynamic', cascade='all, delete-orphan', foreign_keys='MLMCommission.user_id')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_partner(self):
        return self.role == 'partner'

    def get_downline_tree(self, max_depth=3, current_depth=1):
        """Get MLM downline tree up to max_depth levels."""
        tree = []
        for downline in self.downlines:
            node = {
                'user': downline,
                'level': current_depth,
                'children': []
            }
            if current_depth < max_depth:
                node['children'] = downline.get_downline_tree(max_depth, current_depth + 1)
            tree.append(node)
        return tree

    def __repr__(self):
        return f'<User {self.email}>'


class Category(db.Model):
    """Product category with optional hierarchical structure."""
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(256))
    icon = db.Column(db.String(50))  # CSS icon class
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    display_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    parent = db.relationship('Category', remote_side=[id], backref='subcategories')
    products = db.relationship('Product', backref='category', lazy='dynamic')

    def __repr__(self):
        return f'<Category {self.name}>'


class Product(db.Model):
    """Product listing with pricing, stock, and metadata."""
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=True)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    short_description = db.Column(db.String(300))
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=True)
    mrp = db.Column(db.Float, nullable=True)
    weight = db.Column(db.String(50))
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    image_url = db.Column(db.String(256))
    image_url_2 = db.Column(db.String(256))
    stock = db.Column(db.Integer, default=100)
    rating = db.Column(db.Float, default=4.0)
    review_count = db.Column(db.Integer, default=0)
    is_new = db.Column(db.Boolean, default=False)
    is_bestseller = db.Column(db.Boolean, default=False)
    is_featured = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    brand = db.Column(db.String(100))
    shade_name = db.Column(db.String(100))
    shade_color = db.Column(db.String(20)) # Hex color code or CSS color name
    shade_color_2 = db.Column(db.String(20)) # Second color for duo shades
    parent_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    tags = db.Column(db.String(500))  # Comma-separated tags
    how_to_use = db.Column(db.Text)
    ingredients = db.Column(db.Text)

    # Relationships
    variants = db.relationship('Product', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')
    images = db.relationship('ProductImage', backref='product', lazy='dynamic', cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='product', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def discount_percent(self):
        if self.mrp and self.mrp > self.price:
            return round(((self.mrp - self.price) / self.mrp) * 100)
        return 0

    @property
    def in_stock(self):
        return self.stock > 0

    def __repr__(self):
        return f'<Product {self.name}>'


class ProductImage(db.Model):
    """Additional images for a product gallery."""
    __tablename__ = 'product_images'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    image_url = db.Column(db.String(512), nullable=False)
    media_type = db.Column(db.String(20), default='image') # 'image' or 'video'
    display_order = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<ProductImage {self.image_url}>'


class Catalogue(db.Model):
    """Monthly eCatalogue."""
    __tablename__ = 'catalogues'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    month_year = db.Column(db.String(50), nullable=False)  # e.g., 'April 2026'
    cover_image = db.Column(db.String(256), nullable=False)
    file_url = db.Column(db.String(256), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    is_coming_soon = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Catalogue {self.title}>'


class Cart(db.Model):
    """Shopping cart for a user."""
    __tablename__ = 'carts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    items = db.relationship('CartItem', backref='cart', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def total(self):
        return sum(item.subtotal for item in self.items)

    @property
    def item_count(self):
        return sum(item.quantity for item in self.items)

    def __repr__(self):
        return f'<Cart user={self.user_id}>'


class CartItem(db.Model):
    """Individual item in a shopping cart."""
    __tablename__ = 'cart_items'

    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('carts.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    product = db.relationship('Product')

    @property
    def subtotal(self):
        return self.product.price * self.quantity

    def __repr__(self):
        return f'<CartItem product={self.product_id} qty={self.quantity}>'


class Address(db.Model):
    """User shipping/billing address."""
    __tablename__ = 'addresses'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    address_line1 = db.Column(db.String(200), nullable=False)
    address_line2 = db.Column(db.String(200))
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    pincode = db.Column(db.String(10), nullable=False)
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def full_address(self):
        parts = [self.address_line1]
        if self.address_line2:
            parts.append(self.address_line2)
        parts.extend([self.city, self.state, self.pincode])
        return ', '.join(parts)

    def __repr__(self):
        return f'<Address {self.city}, {self.state}>'


class Order(db.Model):
    """Customer order with items and payment."""
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subtotal = db.Column(db.Float, nullable=False)
    shipping_fee = db.Column(db.Float, default=0.0)
    discount = db.Column(db.Float, default=0.0)
    total = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, shipped, delivered, cancelled
    payment_method = db.Column(db.String(30))  # card, upi, cod, wallet
    payment_status = db.Column(db.String(20), default='pending')  # pending, paid, failed, refunded
    shipping_name = db.Column(db.String(100))
    shipping_phone = db.Column(db.String(15))
    shipping_address = db.Column(db.Text)
    shipping_city = db.Column(db.String(100))
    shipping_state = db.Column(db.String(100))
    shipping_pincode = db.Column(db.String(10))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy='dynamic', cascade='all, delete-orphan')
    transactions = db.relationship('Transaction', backref='order', lazy='dynamic', cascade='all, delete-orphan')
    commissions = db.relationship('MLMCommission', backref='order', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Order {self.order_number}>'


class OrderItem(db.Model):
    """Individual item in an order."""
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    product_name = db.Column(db.String(200), nullable=False)
    product_image = db.Column(db.String(256))
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    mrp = db.Column(db.Float)

    # Relationships
    product = db.relationship('Product')

    @property
    def subtotal(self):
        return self.price * self.quantity

    def __repr__(self):
        return f'<OrderItem {self.product_name}>'


class Transaction(db.Model):
    """Payment transaction record."""
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    transaction_ref = db.Column(db.String(50), unique=True, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    method = db.Column(db.String(30), nullable=False)  # card, upi, cod, wallet
    status = db.Column(db.String(20), default='pending')  # pending, success, failed, refunded
    card_last4 = db.Column(db.String(4))
    upi_id = db.Column(db.String(100))
    gateway_response = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Transaction {self.transaction_ref}>'


class MLMCommission(db.Model):
    """MLM commission earned by a user from a downline's order."""
    __tablename__ = 'mlm_commissions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    from_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    level = db.Column(db.Integer, nullable=False)  # 1, 2, or 3
    rate = db.Column(db.Float, nullable=False)  # Commission rate applied
    status = db.Column(db.String(20), default='pending')  # pending, approved, paid
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    from_user = db.relationship('User', foreign_keys=[from_user_id])

    def __repr__(self):
        return f'<MLMCommission L{self.level} ₹{self.amount}>'


class Wishlist(db.Model):
    """User product wishlist."""
    __tablename__ = 'wishlists'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    product = db.relationship('Product')

    # Unique constraint
    __table_args__ = (db.UniqueConstraint('user_id', 'product_id', name='unique_wishlist_item'),)

    def __repr__(self):
        return f'<Wishlist user={self.user_id} product={self.product_id}>'


class BlogPost(db.Model):
    """Daily blog post managed by admin."""
    __tablename__ = 'blog_posts'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    slug = db.Column(db.String(300), unique=True, nullable=False)
    summary = db.Column(db.String(500))
    content = db.Column(db.Text, nullable=False)
    cover_image = db.Column(db.String(512))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<BlogPost {self.title}>'
class ContactMessage(db.Model):
    """Messages from the contact form."""
    __tablename__ = 'contact_messages'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200))
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ContactMessage from {self.email}>'


class Review(db.Model):
    """Product ratings and feedback from users."""
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False, default=5)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    author = db.relationship('User', backref=db.backref('reviews', lazy='dynamic'))

    def __repr__(self):
        return f'<Review {self.rating}* by User {self.user_id} for Product {self.product_id}>'
