"""
Oriflame E-Commerce & MLM Platform — Main Application
Flask application with all routes for the public store, user dashboard, and admin panel.
"""
import os
import uuid
from datetime import datetime
from functools import wraps
import razorpay

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, jsonify, abort, session
)
from werkzeug.utils import secure_filename
from flask_login import (
    LoginManager, login_user, logout_user, login_required, current_user
)

from config import Config, BASE_DIR
from flask_migrate import Migrate
from models import (
    db, User, Category, Product, ProductImage, Catalogue, Cart, CartItem,
    Address, Order, OrderItem, Transaction, MLMCommission, Wishlist, BlogPost, ContactMessage, Review
)

# ─── App Factory ──────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config.from_object(Config)

# Razorpay Client
try:
    razorpay_client = razorpay.Client(auth=(Config.RAZORPAY_KEY_ID, Config.RAZORPAY_KEY_SECRET))
    razorpay_client.set_app_details({"title": "Oriflame-E-Commerce", "version": "1.0.0"})
    print(f"[RAZORPAY] Initialized with Key ID: {Config.RAZORPAY_KEY_ID[:8]}...")
except Exception as e:
    print(f"[RAZORPAY] Error initializing client: {str(e)}")
    razorpay_client = None

# Ensure database directory exists
os.makedirs(os.path.join(BASE_DIR, 'database'), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, 'static', 'images', 'uploads'), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, 'static', 'catalogues'), exist_ok=True)

db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'warning'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ─── Context Processor ───────────────────────────────────────────────────────
@app.context_processor
def inject_globals():
    """Make categories and cart count available in all templates."""
    categories = Category.query.filter_by(is_active=True).order_by(Category.display_order).all()
    cart_count = 0
    wishlist_count = 0
    product_count = 0
    pending_orders = 0
    
    if current_user.is_authenticated:
        if current_user.cart:
            cart_count = current_user.cart.item_count
        wishlist_count = Wishlist.query.filter_by(user_id=current_user.id).count()
        
        if current_user.is_admin:
            product_count = Product.query.count()
            pending_orders = Order.query.filter_by(status='pending').count()
            
    return dict(
        categories=categories, 
        cart_count=cart_count, 
        wishlist_count=wishlist_count,
        product_count=product_count,
        pending_orders=pending_orders
    )


# ─── Admin Required Decorator ────────────────────────────────────────────────
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(404)  # Return 404 to hide admin panel existence
        return f(*args, **kwargs)
    return decorated_function


# ─── Helper Functions ─────────────────────────────────────────────────────────
def generate_order_number():
    return 'ORI' + datetime.utcnow().strftime('%Y%m%d') + str(uuid.uuid4().int)[:6]


def generate_transaction_ref():
    return 'TXN' + str(uuid.uuid4().hex)[:12].upper()


def slugify(text):
    return text.lower().replace(' ', '-').replace('&', 'and').replace("'", '')


def calculate_mlm_commissions(order):
    """Calculate and create MLM commissions for an order."""
    if not order or order.payment_status != 'paid':
        return

    buyer = order.user
    if not buyer:
        return

    commission_rates = Config.MLM_COMMISSION_RATES
    
    current = buyer
    for level in range(1, 4):
        if not current.sponsor_id:
            break
        sponsor = User.query.get(current.sponsor_id)
        if not sponsor or not sponsor.is_partner:
            current = sponsor
            continue
        
        rate = commission_rates.get(level, 0)
        if rate > 0:
            amount = order.subtotal * (rate / 100)
            commission = MLMCommission(
                user_id=sponsor.id,
                order_id=order.id,
                from_user_id=buyer.id,
                amount=round(amount, 2),
                level=level,
                rate=rate,
                status='pending'
            )
            db.session.add(commission)
            sponsor.total_commission += round(amount, 2)
        
        current = sponsor
    
    db.session.commit()


# ═══════════════════════════════════════════════════════════════════════════════
#  PUBLIC ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/')
def home():
    new_arrivals = Product.query.filter_by(is_active=True, is_new=True).order_by(Product.created_at.desc()).limit(8).all()
    bestsellers = Product.query.filter_by(is_active=True, is_bestseller=True).order_by(Product.rating.desc()).limit(8).all()
    featured = Product.query.filter_by(is_active=True, is_featured=True).limit(8).all()
    
    # Fallback if not enough products
    if len(new_arrivals) < 4:
        new_arrivals = Product.query.filter_by(is_active=True).order_by(Product.created_at.desc()).limit(8).all()
    if len(bestsellers) < 4:
        bestsellers = Product.query.filter_by(is_active=True).order_by(Product.rating.desc()).limit(8).all()
    if len(featured) < 4:
        featured = Product.query.filter_by(is_active=True).order_by(Product.price.desc()).limit(8).all()
    
    return render_template('index.html',
                           new_arrivals=new_arrivals,
                           bestsellers=bestsellers,
                           featured=featured)


@app.route('/products')
def products():
    query = Product.query.filter_by(is_active=True)
    
    # Combined Search (handles 'search' or 'q' parameters)
    search_query = request.args.get('search') or request.args.get('q')
    if search_query:
        search_query = search_query.strip()
        query = query.filter(
            db.or_(
                Product.name.ilike(f'%{search_query}%'),
                Product.description.ilike(f'%{search_query}%'),
                Product.code.ilike(f'%{search_query}%'),
                Product.brand.ilike(f'%{search_query}%'),
                Product.tags.ilike(f'%{search_query}%')
            )
        )
    
    # Filter
    filter_type = request.args.get('filter')
    if filter_type == 'new':
        query = query.filter_by(is_new=True)
    elif filter_type == 'bestsellers':
        query = query.filter_by(is_bestseller=True)
    elif filter_type == 'offers':
        query = query.filter(Product.price < Product.mrp)
    
    # Category filter
    cat_slug = request.args.get('category')
    if cat_slug:
        cat = Category.query.filter_by(slug=cat_slug).first()
        if cat:
            query = query.filter_by(category_id=cat.id)
            
    # Brand filter
    brand = request.args.get('brand')
    if brand:
        query = query.filter(Product.brand.ilike(brand))
    
    # Price range filter
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    
    # Sort
    sort = request.args.get('sort', 'random')
    if sort == 'price_low':
        query = query.order_by(Product.price.asc())
    elif sort == 'price_high':
        query = query.order_by(Product.price.desc())
    elif sort == 'rating':
        query = query.order_by(Product.rating.desc())
    elif sort == 'popular':
        query = query.order_by(Product.review_count.desc())
    elif sort == 'newest':
        query = query.order_by(Product.created_at.desc())
    else:
        seed = session.get('random_sort_seed')
        if not seed:
            import random
            seed = random.randint(1, 100000)
            session['random_sort_seed'] = seed
        query = query.order_by((Product.id * seed % 100003).asc())
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = Config.PRODUCTS_PER_PAGE
    
    # Get all active products that match criteria
    all_matching = query.all()
    
    # Grouping Logic: Consolidate variants into parent products
    # We want to show only the 'root' product in the grid
    grouped_products = []
    seen_roots = {} # root_id or name -> product object
    variants_map = {} # root_id or name -> list of variant products
    name_to_root = {} # name -> root_id
    
    for p in all_matching:
        # Determine root identifier
        root_id = p.parent_id
        
        if not root_id:
            # Check if we've seen this name before
            clean_name = p.name.strip().lower()
            if clean_name in name_to_root:
                root_id = name_to_root[clean_name]
            else:
                root_id = f"name_{clean_name}"
                name_to_root[clean_name] = root_id

        if root_id not in seen_roots:
            seen_roots[root_id] = p
            variants_map[p.id] = [] # Store variants by the ID of the 'root' product we picked
        else:
            # It's a variant
            root_product = seen_roots[root_id]
            if p.id != root_product.id:
                if root_product.id not in variants_map:
                    variants_map[root_product.id] = []
                variants_map[root_product.id].append(p)
                
    # Flatten the grouped products
    products_list = list(seen_roots.values())
    
    # Re-apply sorting to the grouped list (since order might have changed)
    # (Simplified: we use the original query's order for roots)
    
    total = len(products_list)
    total_pages = (total + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    paginated_products = products_list[start:end]
    
    # Pass variants to the template
    return render_template('products.html',
                           products=paginated_products,
                           variants_map=variants_map,
                           page=page,
                           total_pages=total_pages,
                           category=None)


@app.route('/category/<slug>')
def category_page(slug):
    category = Category.query.filter_by(slug=slug, is_active=True).first_or_404()
    
    query = Product.query.filter_by(category_id=category.id, is_active=True)
    
    # Price range filter
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    sort = request.args.get('sort', 'random')
    if sort == 'price_low':
        query = query.order_by(Product.price.asc())
    elif sort == 'price_high':
        query = query.order_by(Product.price.desc())
    elif sort == 'rating':
        query = query.order_by(Product.rating.desc())
    elif sort == 'newest':
        query = query.order_by(Product.created_at.desc())
    else:
        seed = session.get('random_sort_seed')
        if not seed:
            import random
            seed = random.randint(1, 100000)
            session['random_sort_seed'] = seed
        query = query.order_by((Product.id * seed % 100003).asc())
    
    page = request.args.get('page', 1, type=int)
    per_page = Config.PRODUCTS_PER_PAGE
    total = query.count()
    total_pages = (total + per_page - 1) // per_page
    products_list = query.offset((page - 1) * per_page).limit(per_page).all()
    
    return render_template('products.html',
                           products=products_list,
                           category=category,
                           page=page,
                           total_pages=total_pages)


@app.route('/products/<slug>')
def product_detail(slug):
    product = Product.query.filter_by(slug=slug, is_active=True).first_or_404()
    
    # Find variants (sharing the same parent or being children of this product)
    from sqlalchemy import or_
    root_id = product.parent_id if product.parent_id else product.id
    variants = Product.query.filter(
        or_(Product.id == root_id, Product.parent_id == root_id),
        Product.id != product.id,
        Product.is_active == True
    ).all()

    # IF no variants found by ID (orphans), try finding by name similarity (Super Robust)
    if not variants:
        clean_name = product.name.strip()
        
        # 1. Try exact name match (best for products where shades share the same name)
        variants = Product.query.filter(
            Product.name.ilike(clean_name),
            Product.id != product.id,
            Product.is_active == True
        ).all()
        
        # 2. If still nothing, try matching by the first 3 words (more specific than 2)
        if not variants:
            name_parts = clean_name.split()
            if len(name_parts) >= 3:
                search_prefix = " ".join(name_parts[:3])
                variants = Product.query.filter(
                    Product.name.ilike(f"{search_prefix}%"),
                    Product.id != product.id,
                    Product.is_active == True
                ).all()
            # 3. Last resort: match by first 2 words if they are long enough
            elif len(name_parts) >= 2 and len(name_parts[0]) > 3:
                search_prefix = " ".join(name_parts[:2])
                variants = Product.query.filter(
                    Product.name.ilike(f"{search_prefix}%"),
                    Product.id != product.id,
                    Product.is_active == True
                ).all()
    
    # Find related products
    related = Product.query.filter(
        Product.category_id == product.category_id,
        Product.id != product.id,
        Product.name != product.name,
        Product.is_active == True
    ).limit(4).all()

    # Check wishlist status
    is_in_wishlist = False
    if current_user.is_authenticated:
        is_in_wishlist = Wishlist.query.filter_by(
            user_id=current_user.id, 
            product_id=product.id
        ).first() is not None
    
    return render_template('product_detail.html', 
                           product=product, 
                           variants=variants, 
                           related_products=related,
                           is_in_wishlist=is_in_wishlist,
                           Review=Review)


@app.route('/product/<int:product_id>/review', methods=['POST'])
@login_required
def submit_review(product_id):
    product = Product.query.get_or_404(product_id)
    rating = request.form.get('rating', type=int)
    comment = request.form.get('comment')
    
    if rating and comment:
        review = Review(
            product_id=product.id,
            user_id=current_user.id,
            rating=rating,
            comment=comment
        )
        db.session.add(review)
        
        # Update product average rating (simple logic)
        all_reviews = product.reviews.all()
        total_rating = sum([r.rating for r in all_reviews]) + rating
        product.review_count = len(all_reviews) + 1
        product.rating = round(total_rating / product.review_count, 1)
        
        db.session.commit()
        flash('Thank you for your feedback!', 'success')
    else:
        flash('Please provide both a rating and a comment.', 'warning')
        
    return redirect(url_for('product_detail', slug=product.slug))


@app.route('/join')
def join_page():
    return render_template('join.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact_page():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message_text = request.form.get('message')
        
        # Debug log
        with open('contact_debug.log', 'a') as f:
            f.write(f"{datetime.now()}: POST received from {email}. Fields: {first_name}, {last_name}, {subject}\n")
        
        if first_name and last_name and email and message_text:
            try:
                msg = ContactMessage(
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    subject=subject,
                    message=message_text
                )
                db.session.add(msg)
                db.session.commit()
                flash('Thank you for your message! Our team will get back to you shortly.', 'success')
                with open('contact_debug.log', 'a') as f:
                    f.write(f"{datetime.now()}: SUCCESS - Message saved to DB (ID: {msg.id})\n")
            except Exception as e:
                db.session.rollback()
                flash(f'An error occurred: {str(e)}', 'danger')
                with open('contact_debug.log', 'a') as f:
                    f.write(f"{datetime.now()}: ERROR - {str(e)}\n")
        else:
            flash('Please fill in all required fields.', 'danger')
            with open('contact_debug.log', 'a') as f:
                f.write(f"{datetime.now()}: VALIDATION FAILED - Missing fields\n")
            
        return redirect(url_for('contact_page'))
    return render_template('contact.html')


@app.route('/search')
def search_page():
    return redirect(url_for('products', search=request.args.get('q', '')))


@app.route('/catalogue')
def catalogue_page():
    catalogues = Catalogue.query.filter_by(is_active=True).order_by(Catalogue.created_at.desc()).all()
    return render_template('catalogue.html', catalogues=catalogues)


@app.route('/catalogue/<int:cat_id>')
def catalogue_view(cat_id):
    cat = Catalogue.query.filter_by(id=cat_id, is_active=True).first_or_404()
    return render_template('catalogue_view.html', cat=cat)


@app.route('/blog')
def blog_page():
    posts = BlogPost.query.filter_by(is_active=True).order_by(BlogPost.created_at.desc()).all()
    return render_template('blog.html', posts=posts)


@app.route('/blog/<slug>')
def blog_detail(slug):
    post = BlogPost.query.filter_by(slug=slug, is_active=True).first_or_404()
    recent_posts = BlogPost.query.filter(
        BlogPost.id != post.id, BlogPost.is_active == True
    ).order_by(BlogPost.created_at.desc()).limit(5).all()
    return render_template('blog_detail.html', post=post, recent_posts=recent_posts)


# ═══════════════════════════════════════════════════════════════════════════════
#  AUTH ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact support.', 'error')
                return render_template('login.html')
            
            login_user(user, remember=remember)
            flash(f'Welcome back, {user.first_name}!', 'success')
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            if user.is_admin:
                return redirect('/oriflame-admin-panel-x9k2/')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        phone = request.form.get('phone', '').strip()
        role = request.form.get('role', 'customer')
        sponsor_code = request.form.get('sponsor_code', '').strip()
        
        # Validation
        if not all([email, password, first_name, last_name]):
            flash('Please fill in all required fields.', 'error')
            return render_template('register.html')
        
        if password != confirm:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return render_template('register.html')
        
        # Find sponsor
        sponsor_id = None
        if sponsor_code and role == 'partner':
            try:
                code_num = int(sponsor_code.replace('ORI', ''))
                sponsor_user_id = (code_num - 5000) // 1000
                sponsor = User.query.get(sponsor_user_id)
                if sponsor:
                    sponsor_id = sponsor.id
            except (ValueError, TypeError):
                pass
        
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role=role if role in ['customer', 'partner'] else 'customer',
            sponsor_id=sponsor_id
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        flash(f'Welcome to Oriflame, {first_name}! Your account has been created.', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))


# ═══════════════════════════════════════════════════════════════════════════════
#  CART ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/cart')
@login_required
def view_cart():
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    cart_items = []
    cart_total = 0
    
    if cart:
        cart_items = cart.items.all()
        cart_total = cart.total
    
    return render_template('cart.html', cart_items=cart_items, cart_total=cart_total)


@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Please login first', 'redirect': '/login'})
    
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    
    product = Product.query.get(product_id)
    if not product or not product.is_active:
        return jsonify({'success': False, 'message': 'Product not found'})
    
    if not product.in_stock:
        return jsonify({'success': False, 'message': 'Product is out of stock'})
    
    # Get or create cart
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart:
        cart = Cart(user_id=current_user.id)
        db.session.add(cart)
        db.session.flush()
    
    # Check if product already in cart
    existing = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()
    if existing:
        existing.quantity += int(quantity)
    else:
        item = CartItem(cart_id=cart.id, product_id=product_id, quantity=int(quantity))
        db.session.add(item)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'{product.name} added to cart!',
        'cart_count': cart.item_count
    })


@app.route('/cart/items')
@login_required
def get_cart_items():
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    
    if not cart:
        return jsonify({'items': [], 'total': 0, 'count': 0})
    
    items = []
    for item in cart.items:
        items.append({
            'id': item.id,
            'product_id': item.product_id,
            'name': item.product.name,
            'price': item.product.price,
            'image': item.product.image_url or '/static/images/placeholder.png',
            'quantity': item.quantity,
            'subtotal': item.subtotal
        })
    
    return jsonify({
        'items': items,
        'total': cart.total,
        'count': cart.item_count
    })


@app.route('/cart/update', methods=['POST'])
@login_required
def update_cart():
    data = request.get_json()
    item_id = data.get('item_id')
    quantity = data.get('quantity', 1)
    
    item = CartItem.query.get(item_id)
    if not item or item.cart.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Item not found'})
    
    if quantity < 1:
        db.session.delete(item)
    else:
        item.quantity = min(quantity, item.product.stock)
    
    db.session.commit()
    return jsonify({'success': True})


@app.route('/cart/remove', methods=['POST'])
@login_required
def remove_from_cart():
    data = request.get_json()
    item_id = data.get('item_id')
    
    item = CartItem.query.get(item_id)
    if not item or item.cart.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Item not found'})
    
    db.session.delete(item)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Item removed'})


# ═══════════════════════════════════════════════════════════════════════════════
#  CHECKOUT & PAYMENT ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart or cart.item_count == 0:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('products'))
    
    cart_items = cart.items.all()
    cart_total = cart.total
    addresses = Address.query.filter_by(user_id=current_user.id).all()
    
    if request.method == 'POST':
        # Create order
        shipping_fee = 0 if cart_total >= 999 else 99
        order = Order(
            order_number=generate_order_number(),
            user_id=current_user.id,
            subtotal=cart_total,
            shipping_fee=shipping_fee,
            total=cart_total + shipping_fee,
            payment_method=request.form.get('payment_method', 'cod'),
            shipping_name=request.form.get('shipping_name'),
            shipping_phone=request.form.get('shipping_phone'),
            shipping_address=request.form.get('shipping_address'),
            shipping_city=request.form.get('shipping_city'),
            shipping_state=request.form.get('shipping_state'),
            shipping_pincode=request.form.get('shipping_pincode'),
            notes=request.form.get('notes')
        )
        db.session.add(order)
        db.session.flush()
        
        # Create order items
        for item in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                product_name=item.product.name,
                product_image=item.product.image_url,
                quantity=item.quantity,
                price=item.product.price,
                mrp=item.product.mrp
            )
            db.session.add(order_item)
            
            # Decrease stock
            item.product.stock -= item.quantity
        
        # Save address if new
        if request.form.get('shipping_name'):
            existing_addr = Address.query.filter_by(
                user_id=current_user.id,
                pincode=request.form.get('shipping_pincode')
            ).first()
            if not existing_addr:
                addr = Address(
                    user_id=current_user.id,
                    full_name=request.form.get('shipping_name'),
                    phone=request.form.get('shipping_phone'),
                    address_line1=request.form.get('shipping_address'),
                    city=request.form.get('shipping_city'),
                    state=request.form.get('shipping_state'),
                    pincode=request.form.get('shipping_pincode'),
                    is_default=len(addresses) == 0
                )
                db.session.add(addr)
        
        # Clear cart
        for item in cart_items:
            db.session.delete(item)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'order_id': order.id,
            'order_number': order.order_number
        })
    
    return render_template('checkout.html',
                           cart_items=cart_items,
                           cart_total=cart_total,
                           addresses=addresses,
                           razorpay_key_id=Config.RAZORPAY_KEY_ID)


@app.route('/wishlist/toggle/<int:product_id>', methods=['POST'])
@login_required
def toggle_wishlist(product_id):
    item = Wishlist.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if item:
        db.session.delete(item)
        db.session.commit()
        return jsonify({'success': True, 'status': 'removed', 'message': 'Removed from wishlist'})
    else:
        new_item = Wishlist(user_id=current_user.id, product_id=product_id)
        db.session.add(new_item)
        db.session.commit()
        return jsonify({'success': True, 'status': 'added', 'message': 'Added to wishlist'})

@app.route('/wishlist')
@login_required
def wishlist():
    items = Wishlist.query.filter_by(user_id=current_user.id).all()
    return render_template('wishlist.html', items=items)


@app.route('/payment/process', methods=['POST'])

@login_required
def process_payment():
    data = request.get_json()
    order_id = data.get('order_id')
    
    order = Order.query.get(order_id)
    if not order or order.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Order not found'})
    
    # Handle Wallet payment specifically
    if order.payment_method == 'wallet':
        if current_user.total_commission < order.total:
            return jsonify({'success': False, 'message': 'Insufficient wallet balance'})
        
        current_user.total_commission -= order.total
    
    # Create transaction record
    transaction = Transaction(
        order_id=order.id,
        transaction_ref=generate_transaction_ref(),
        amount=order.total,
        method=order.payment_method,
        status='success' if order.payment_method != 'cod' else 'pending'
    )
    db.session.add(transaction)
    
    # Update order status
    order.status = 'confirmed'
    
    if order.payment_method != 'cod':
        order.payment_status = 'paid'
        # Update user's total sales for paid orders
        current_user.total_sales += order.total
        # Calculate MLM commissions
        calculate_mlm_commissions(order)
    else:
        order.payment_status = 'pending'
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'order_number': order.order_number,
        'transaction_ref': transaction.transaction_ref
    })


@app.route('/api/create-order', methods=['POST'])
@login_required
def create_razorpay_order():
    """Create a Razorpay order for the frontend modal."""
    try:
        print("[RAZORPAY] Received request to create order", flush=True)
        data = request.get_json()
        order_id = data.get('order_id')
        
        if not order_id:
            print("[RAZORPAY] Error: No order_id provided in request", flush=True)
            return jsonify({'success': False, 'message': 'No order_id provided'}), 400
            
        order = Order.query.get(order_id)
        if not order or order.user_id != current_user.id:
            print(f"[RAZORPAY] Error: Order {order_id} not found for user {current_user.id}", flush=True)
            return jsonify({'success': False, 'message': 'Order not found'}), 404
            
        if order.total is None:
            print(f"[RAZORPAY] Error: Order {order_id} has no total amount", flush=True)
            return jsonify({'success': False, 'message': 'Order total is missing'}), 400

        amount = int(order.total * 100) # amount in paise
        print(f"[RAZORPAY] Creating order for amount: {amount} paise (Order #{order.order_number})", flush=True)
        
        if not razorpay_client:
            print("[RAZORPAY] Error: Razorpay client not initialized", flush=True)
            return jsonify({'success': False, 'message': 'Razorpay service unavailable'}), 500
            
        razorpay_order = razorpay_client.order.create({
            'amount': amount,
            'currency': 'INR',
            'receipt': str(order.order_number),
            'payment_capture': '1'
        })
        print(f"[RAZORPAY] Order created successfully: {razorpay_order['id']}", flush=True)
        return jsonify({
            'order_id': razorpay_order['id'],
            'amount': razorpay_order['amount'],
            'currency': razorpay_order['currency']
        })
    except Exception as e:
        import traceback
        print(f"[RAZORPAY] Exception during order creation: {str(e)}", flush=True)
        print(traceback.format_exc(), flush=True)
        # Fallback to allow checkout without Razorpay during development
        return jsonify({
            'success': False, 
            'message': f"Razorpay Error: {str(e)}",
            'mock_fallback': True
        }), 200


@app.route('/api/verify-payment', methods=['POST'])
@login_required
def verify_payment():
    """Verify the Razorpay payment signature."""
    print("[RAZORPAY] Received request to verify payment")
    data = request.get_json()
    
    razorpay_payment_id = data.get('razorpay_payment_id')
    razorpay_order_id = data.get('razorpay_order_id')
    razorpay_signature = data.get('razorpay_signature')
    local_order_id = data.get('order_id')
    
    if not all([razorpay_payment_id, razorpay_order_id, razorpay_signature, local_order_id]):
        print("[RAZORPAY] Error: Missing payment verification fields")
        return jsonify({'success': False, 'message': 'Missing payment details'}), 400
        
    if not razorpay_client:
        print("[RAZORPAY] Error: Razorpay client not initialized for verification")
        return jsonify({'success': False, 'message': 'Razorpay service unavailable'}), 500

    # Verify signature
    params_dict = {
        'razorpay_order_id': razorpay_order_id,
        'razorpay_payment_id': razorpay_payment_id,
        'razorpay_signature': razorpay_signature
    }
    
    try:
        print(f"[RAZORPAY] Verifying signature for Payment ID: {razorpay_payment_id}")
        razorpay_client.utility.verify_payment_signature(params_dict)
        
        # If verification is successful, update the order
        order = Order.query.get(local_order_id)
        if order and order.user_id == current_user.id:
            print(f"[RAZORPAY] Success: Signature verified. Confirming Order {local_order_id}")
            # Create transaction record
            transaction = Transaction(
                order_id=order.id,
                transaction_ref=razorpay_payment_id,
                amount=order.total,
                method=order.payment_method,
                status='success',
                gateway_response=str(data)
            )
            db.session.add(transaction)
            
            # Update order status ONLY if it wasn't already cancelled
            if order.status != 'cancelled':
                order.status = 'confirmed'
            
            order.payment_status = 'paid'
            
            # Update user's total sales
            current_user.total_sales += order.total
            
            # Calculate MLM commissions
            calculate_mlm_commissions(order)
            
            db.session.commit()
            print(f"[RAZORPAY] Order confirmed successfully: {order.order_number}")
            
            return jsonify({
                'success': True,
                'order_number': order.order_number,
                'transaction_ref': razorpay_payment_id
            })
        else:
            print(f"[RAZORPAY] Error: Order {local_order_id} not found during verification")
            return jsonify({'success': False, 'message': 'Order not found'}), 404
            
    except razorpay.errors.SignatureVerificationError as e:
        print(f"[RAZORPAY] Error: Signature verification failed - {str(e)}")
        return jsonify({'success': False, 'message': 'Payment verification failed'}), 400
    except Exception as e:
        print(f"[RAZORPAY] Exception during verification: {str(e)}")
        return jsonify({'success': False, 'message': f"Verification error: {str(e)}"}), 500


# ═══════════════════════════════════════════════════════════════════════════════
#  USER DASHBOARD ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/dashboard')
@login_required
def dashboard():
    order_count = Order.query.filter_by(user_id=current_user.id).filter(Order.status != 'cancelled').count()
    total_spent = db.session.query(db.func.sum(Order.total)).filter_by(
        user_id=current_user.id, payment_status='paid'
    ).filter(Order.status != 'cancelled').scalar() or 0
    
    downline_count = len(current_user.downlines) if current_user.is_partner else 0
    wishlist_count = Wishlist.query.filter_by(user_id=current_user.id).count()
    review_count = 0
    
    recent_orders = Order.query.filter_by(user_id=current_user.id).order_by(
        Order.created_at.desc()
    ).limit(5).all()
    
    return render_template('dashboard.html',
                           order_count=order_count,
                           total_spent=total_spent,
                           downline_count=downline_count,
                           wishlist_count=wishlist_count,
                           review_count=review_count,
                           recent_orders=recent_orders)


@app.route('/orders')
@login_required
def user_orders():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(
        Order.created_at.desc()
    ).all()
    return render_template('orders.html', orders=orders)


@app.route('/orders/<int:order_id>/cancel', methods=['POST'])
@login_required
def cancel_order(order_id):
    order = Order.query.get_or_404(order_id)
    
    # Security check: ensure the order belongs to the current user
    if order.user_id != current_user.id:
        abort(403)
    
    # Check if the order can be cancelled
    if order.status not in ['pending', 'confirmed']:
        flash('This order cannot be cancelled as it has already been processed or shipped.', 'warning')
        return redirect(url_for('user_orders'))
    
    try:
        # Update order status
        order.status = 'cancelled'
        
        # Restore stock
        for item in order.items:
            item.product.stock += item.quantity
        
        # Reverse sales and commissions if already processed
        if order.payment_status == 'paid':
            # Subtract from user's total sales
            current_user.total_sales = max(0, current_user.total_sales - order.total)
            
            # Handle Transactions
            for txn in order.transactions:
                txn.status = 'refunded'
            
            # Handle Commissions
            commissions = MLMCommission.query.filter_by(order_id=order.id).all()
            for comm in commissions:
                sponsor = User.query.get(comm.user_id)
                if sponsor:
                    sponsor.total_commission = max(0, sponsor.total_commission - comm.amount)
                db.session.delete(comm)
            
            order.payment_status = 'refunded'
            
        db.session.commit()
        flash(f'Order #{order.order_number} has been cancelled successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error cancelling order: {str(e)}', 'danger')
        
    return redirect(url_for('user_orders'))


@app.route('/mlm/network')
@login_required
def mlm_network():
    if not current_user.is_partner:
        flash('Become a Brand Partner to access MLM features.', 'info')
        return redirect(url_for('join_page'))
    
    downline_tree = current_user.get_downline_tree(max_depth=3)
    total_downlines = len(current_user.downlines)
    
    # Calculate total network sales
    network_sales = 0
    for dl in current_user.downlines:
        network_sales += dl.total_sales
    
    commissions = MLMCommission.query.filter_by(user_id=current_user.id).order_by(
        MLMCommission.created_at.desc()
    ).all()
    
    return render_template('mlm_network.html',
                           downline_tree=downline_tree,
                           total_downlines=total_downlines,
                           network_sales=network_sales,
                           commissions=commissions)


@app.route('/mlm/user/<int:user_id>')
@login_required
def mlm_user_details(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({
        'success': True,
        'user': {
            'name': user.full_name,
            'email': user.email,
            'role': user.role,
            'total_sales': user.total_sales,
            'total_commission': user.total_commission,
            'downline_count': len(user.downlines),
            'join_date': user.join_date.strftime('%d %b %Y')
        }
    })


# ═══════════════════════════════════════════════════════════════════════════════
#  ADMIN ROUTES (Hidden URL)
# ═══════════════════════════════════════════════════════════════════════════════

# ─── Admin Redirects (Convenience) ──────────────────────────────────────────
@app.route('/admin')
@app.route('/admin/products')
@login_required
def admin_convenience_redirect():
    if current_user.is_admin:
        if 'products' in request.path:
            return redirect('/oriflame-admin-panel-x9k2/products')
        return redirect('/oriflame-admin-panel-x9k2/')
    abort(404)

@app.route('/oriflame-admin-panel-x9k2/')
@login_required
@admin_required
def admin_dashboard():
    total_revenue = db.session.query(db.func.sum(Order.total)).filter_by(payment_status='paid').filter(Order.status != 'cancelled').scalar() or 0
    total_orders = Order.query.filter(Order.status != 'cancelled').count()
    total_users = User.query.count()
    total_partners = User.query.filter_by(role='partner').count()
    
    pending_count = Order.query.filter_by(status='pending').count()
    confirmed_count = Order.query.filter_by(status='confirmed').count()
    shipped_count = Order.query.filter_by(status='shipped').count()
    delivered_count = Order.query.filter_by(status='delivered').count()
    
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html',
                           total_revenue=total_revenue,
                           total_orders=total_orders,
                           total_users=total_users,
                           total_partners=total_partners,
                           pending_count=pending_count,
                           confirmed_count=confirmed_count,
                           shipped_count=shipped_count,
                           delivered_count=delivered_count,
                           recent_orders=recent_orders)


@app.route('/oriflame-admin-panel-x9k2/products', methods=['GET'])
@login_required
@admin_required
def admin_products():
    # Fetch all products in one single query to be super fast
    all_products = Product.query.order_by(Product.created_at.desc()).all()
    
    # Separate parents and group variants
    parents = [p for p in all_products if not p.parent_id]
    variants_map = {}
    
    # First pass: Handle explicit parent_id
    for p in all_products:
        if p.parent_id:
            if p.parent_id not in variants_map:
                variants_map[p.parent_id] = []
            variants_map[p.parent_id].append(p)

    # Second pass: For parents with no variants, try name-based grouping for existing data
    remaining_parents = [p for p in parents if p.id not in variants_map]
    orphans = [p for p in all_products if p.parent_id is None]
    
    for p in remaining_parents:
        name_parts = p.name.split()
        if len(name_parts) >= 2:
            base = " ".join(name_parts[:2]).lower()
            # Find products that start with this base but aren't the parent itself
            similar = [o for o in orphans if o.id != p.id and o.name.lower().startswith(base)]
            if similar:
                variants_map[p.id] = similar
                # Remove these from the parents list so they don't show up twice
                for s in similar:
                    if s in parents:
                        parents.remove(s)
            
    categories_list = Category.query.all()
    return render_template('admin/products.html', 
                           products=parents, 
                           all_products=all_products,
                           variants_map=variants_map,
                           categories=categories_list)


@app.route('/oriflame-admin-panel-x9k2/products', methods=['POST'])
@app.route('/oriflame-admin-panel-x9k2/products/<int:product_id>', methods=['POST'])
@login_required
@admin_required
def admin_save_product(product_id=None):
    try:
        form = request.form
        files = request.files.getlist('product_images')
        
        product_name = form.get('name', 'Unnamed Product').strip()
        product_code = form.get('code', '').strip()
        if not product_code:
            product_code = f"ORI{uuid.uuid4().hex[:6].upper()}"
            
        initial_slug = slugify(product_name) if product_name else uuid.uuid4().hex[:10]
        
        if product_id:
            product = Product.query.get_or_404(product_id)
        else:
            product = Product()
            
        # Check if code already exists
        existing_code = Product.query.filter(Product.code == product_code, Product.id != product.id).first()
        if existing_code:
            return jsonify({'success': False, 'message': f'Product code "{product_code}" already exists!'})
            
        product.name = product_name
        product.code = product_code
        product.slug = initial_slug
        
        # Check for slug conflicts
        existing_slug = Product.query.filter(Product.slug == product.slug, Product.id != product.id).first()
        if existing_slug:
            product.slug = f"{initial_slug}-{product.code.lower()}"
            
        # Ensure unique slug even after appending code
        final_check = Product.query.filter(Product.slug == product.slug, Product.id != product.id).first()
        if final_check:
            product.slug = f"{product.slug}-{uuid.uuid4().hex[:4]}"
        
        if not product_id:
            db.session.add(product)
        
        price_val = form.get('price', '').strip()
        product.price = float(price_val) if price_val else 0.0
        
        mrp_val = form.get('mrp', '').strip()
        product.mrp = float(mrp_val) if mrp_val else product.price
        
        cat_id = form.get('category_id', '').strip()
        if cat_id:
            product.category_id = int(cat_id)
            
        stock_val = form.get('stock', '').strip()
        product.stock = int(stock_val) if stock_val else 0
        
        product.brand = form.get('brand')
        product.weight = form.get('weight')
        product.shade_name = form.get('shade_name')
        product.shade_color = form.get('shade_color')
        product.shade_color_2 = form.get('shade_color_2')
        
        p_id = form.get('parent_id', '').strip()
        if p_id:
            product.parent_id = int(p_id)
        else:
            product.parent_id = None
            
        product.short_description = form.get('short_description')
        product.description = form.get('description')
        product.how_to_use = form.get('how_to_use')
        product.ingredients = form.get('ingredients')
        
        product.is_new = bool(form.get('is_new'))
        product.is_bestseller = bool(form.get('is_bestseller'))
        product.is_active = True
        
        # Determine main image from uploaded files first
        main_image_set = False
        if files and files[0].filename != '':
            for i, file in enumerate(files):
                if file and file.filename != '':
                    filename = secure_filename(f"{product.code}_{uuid.uuid4().hex[:8]}_{file.filename}")
                    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(upload_path)
                    
                    img_url = f"/static/images/uploads/{filename}"
                    ext = filename.split('.')[-1].lower()
                    m_type = 'video' if ext in ['mp4', 'webm', 'ogg', 'mov', 'avi'] else 'image'
                    
                    if i == 0 and m_type == 'image':
                        product.image_url = img_url
                        main_image_set = True
                    
                    img_record = ProductImage(product=product, image_url=img_url, media_type=m_type, display_order=i)
                    db.session.add(img_record)
                    
        pasted_urls = form.get('media_urls', '').split('\n')
        for i, url in enumerate(pasted_urls):
            url = url.strip()
            if not url:
                continue
                
            m_type = 'image'
            if 'youtube.com/watch?v=' in url:
                video_id = url.split('v=')[1].split('&')[0]
                url = f"https://www.youtube.com/embed/{video_id}"
                m_type = 'video'
            elif 'youtu.be/' in url:
                video_id = url.split('/')[-1]
                url = f"https://www.youtube.com/embed/{video_id}"
                m_type = 'video'
            
            # First non-video URL becomes main image if not set
            if not main_image_set and m_type == 'image':
                product.image_url = url
                main_image_set = True
            else:
                img_record = ProductImage(product=product, image_url=url, media_type=m_type, display_order=100+i)
                db.session.add(img_record)
        
        # Flush to get the product ID if it's new
        db.session.flush()
        
        # Handle Inline Variants
        v_codes = request.form.getlist('inline_variant_code[]')
        v_names = request.form.getlist('inline_variant_name[]')
        v_colors = request.form.getlist('inline_variant_color[]')
        v_colors2 = request.form.getlist('inline_variant_color2[]')
        v_prices = request.form.getlist('inline_variant_price[]')
        v_mrps = request.form.getlist('inline_variant_mrp[]')
        v_weights = request.form.getlist('inline_variant_weight[]')
        
        for i in range(len(v_codes)):
            code = v_codes[i].strip()
            if not code:
                continue
                
            variant = Product.query.filter_by(code=code).first()
            if not variant:
                variant = Product(code=code)
                db.session.add(variant)
            
            variant.parent_id = product.id
            variant.name = product.name
            variant.slug = slugify(f"{product.name} {code}")
            variant.category_id = product.category_id
            variant.brand = product.brand
            variant.weight = product.weight
            variant.short_description = product.short_description
            variant.description = product.description
            variant.how_to_use = product.how_to_use
            variant.ingredients = product.ingredients
            variant.image_url = product.image_url
            variant.is_new = product.is_new
            variant.is_bestseller = product.is_bestseller
            variant.is_active = True
            
            variant.shade_name = v_names[i].strip() if i < len(v_names) else ''
            variant.shade_color = v_colors[i].strip() if i < len(v_colors) else ''
            variant.shade_color_2 = v_colors2[i].strip() if i < len(v_colors2) else ''
            variant.weight = v_weights[i].strip() if i < len(v_weights) else product.weight
            
            try:
                v_price = float(v_prices[i].strip()) if i < len(v_prices) and v_prices[i].strip() else product.price
                variant.price = v_price
                v_mrp = float(v_mrps[i].strip()) if i < len(v_mrps) and v_mrps[i].strip() else product.mrp
                variant.mrp = v_mrp
            except ValueError:
                variant.price = product.price
                variant.mrp = product.mrp
            
            variant.discount_percent = round(((variant.mrp - variant.price) / variant.mrp) * 100) if variant.mrp > variant.price else 0
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Product and variants saved successfully!'})
        
    except ValueError as ve:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Invalid number format: {str(ve)}'})
    except Exception as e:
        db.session.rollback()
        import traceback
        print(f"[ERROR] saving product: {str(e)}\n{traceback.format_exc()}", flush=True)
        return jsonify({'success': False, 'message': f'Server Error: {str(e)}'})

@app.route('/oriflame-admin-panel-x9k2/api/products/<int:product_id>/variants')
@login_required
def admin_api_product_variants(product_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    variants = Product.query.filter_by(parent_id=product_id).all()
    result = []
    for v in variants:
        result.append({
            'id': v.id,
            'code': v.code,
            'shade_name': v.shade_name or '',
            'shade_color': v.shade_color or '#000000',
            'shade_color_2': v.shade_color_2 or '',
            'price': v.price,
            'mrp': v.mrp,
            'weight': v.weight or ''
        })
    return jsonify(result)


@app.route('/oriflame-admin-panel-x9k2/products/<int:product_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Product permanently removed!'})


@app.route('/oriflame-admin-panel-x9k2/products/<int:product_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def admin_toggle_product_status(product_id):
    product = Product.query.get_or_404(product_id)
    product.is_active = not product.is_active
    db.session.commit()
    status = "Active" if product.is_active else "Inactive"
    return jsonify({'success': True, 'message': f'Product is now {status}!', 'is_active': product.is_active})

@app.route('/oriflame-admin-panel-x9k2/orders', methods=['GET'])
@login_required
@admin_required
def admin_orders():
    orders_list = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin/orders.html', orders=orders_list)


@app.route('/oriflame-admin-panel-x9k2/orders/<int:order_id>/status', methods=['POST'])
@login_required
@admin_required
def admin_update_order_status(order_id):
    data = request.get_json()
    order = Order.query.get_or_404(order_id)
    new_status = data.get('status')
    
    if order.status == 'cancelled' and new_status != 'cancelled':
        return jsonify({'success': False, 'message': 'Cannot change status of a cancelled order.'}), 400
        
    if new_status == 'cancelled' and order.status != 'cancelled':
        # Restore stock
        for item in order.items:
            item.product.stock += item.quantity
            
        # Reverse sales and commissions if already processed
        if order.payment_status == 'paid':
            user = order.user
            if user:
                user.total_sales = max(0, user.total_sales - order.total)
                
            for txn in order.transactions:
                txn.status = 'refunded'
                
            commissions = MLMCommission.query.filter_by(order_id=order.id).all()
            for comm in commissions:
                sponsor = User.query.get(comm.user_id)
                if sponsor:
                    sponsor.total_commission = max(0, sponsor.total_commission - comm.amount)
                db.session.delete(comm)
                
            order.payment_status = 'refunded'

    order.status = new_status or order.status
    db.session.commit()
    return jsonify({'success': True})


@app.route('/oriflame-admin-panel-x9k2/orders/<int:order_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_order(order_id):
    order = Order.query.get_or_404(order_id)
    try:
        # Note: OrderItem and Transaction should be deleted via cascade in models
        db.session.delete(order)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Order deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/oriflame-admin-panel-x9k2/users', methods=['GET'])
@login_required
@admin_required
def admin_users():
    users_list = User.query.order_by(User.join_date.desc()).all()
    return render_template('admin/users.html', users=users_list)


@app.route('/oriflame-admin-panel-x9k2/catalogues', methods=['GET'])
@login_required
@admin_required
def admin_catalogues():
    catalogues_list = Catalogue.query.order_by(Catalogue.created_at.desc()).all()
    return render_template('admin/catalogues.html', catalogues=catalogues_list)

@app.route('/oriflame-admin-panel-x9k2/messages', methods=['GET'])
@login_required
@admin_required
def admin_messages():
    messages_list = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return render_template('admin/messages.html', messages=messages_list)

@app.route('/oriflame-admin-panel-x9k2/messages/<int:msg_id>/toggle-read', methods=['POST'])
@login_required
@admin_required
def admin_toggle_message_read(msg_id):
    msg = ContactMessage.query.get_or_404(msg_id)
    msg.is_read = not msg.is_read
    db.session.commit()
    return jsonify({'success': True, 'is_read': msg.is_read})

@app.route('/oriflame-admin-panel-x9k2/catalogues/<int:cat_id>/delete', methods=['POST'])

@login_required
@admin_required
def admin_delete_catalogue(cat_id):
    cat = Catalogue.query.get_or_404(cat_id)
    db.session.delete(cat)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Catalogue deleted!'})

@app.route('/oriflame-admin-panel-x9k2/catalogues', methods=['POST'])
@login_required
@admin_required
def admin_save_catalogue():
    form = request.form
    cat_id = form.get('id')
    
    if cat_id:
        cat = Catalogue.query.get_or_404(int(cat_id))
    else:
        cat = Catalogue()
        db.session.add(cat)
        
    cat.title = form.get('title')
    cat.month_year = form.get('month_year')
    cat.is_active = bool(form.get('is_active'))
    cat.is_coming_soon = bool(form.get('is_coming_soon'))
    
    # Handle Cover Image Upload
    cover_file = request.files.get('cover_file')
    if cover_file and cover_file.filename:
        filename = secure_filename(cover_file.filename)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        
        dir_path = os.path.join(BASE_DIR, 'static', 'images', 'uploads')
        filepath = os.path.join(dir_path, unique_filename)
        cover_file.save(filepath)
        cat.cover_image = f"/static/images/uploads/{unique_filename}"
    else:
        new_cover_url = form.get('cover_image', '').strip()
        if new_cover_url:
            cat.cover_image = new_cover_url
        elif not getattr(cat, 'cover_image', None):
            return jsonify({'success': False, 'message': 'Cover Image is required. Please upload a file or provide a URL.'})

    # Handle PDF Upload
    pdf_file = request.files.get('pdf_file')
    if pdf_file and pdf_file.filename:
        filename = secure_filename(pdf_file.filename)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        
        dir_path = os.path.join(BASE_DIR, 'static', 'catalogues')
        os.makedirs(dir_path, exist_ok=True)
        
        filepath = os.path.join(dir_path, unique_filename)
        pdf_file.save(filepath)
        cat.file_url = f"/static/catalogues/{unique_filename}"
    else:
        # Fallback to text link if provided
        new_url = form.get('file_url', '').strip()
        if new_url:
            cat.file_url = new_url
        elif not getattr(cat, 'file_url', None) and not cat.is_coming_soon:
            return jsonify({'success': False, 'message': 'PDF File is required for active catalogues. (Optional for Coming Soon)'})
    
    try:
        db.session.commit()
        return jsonify({'success': True, 'message': 'Catalogue saved successfully!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f"Database Error: {str(e)}"})


@app.route('/oriflame-admin-panel-x9k2/users/<int:user_id>/role', methods=['POST'])
@login_required
@admin_required
def admin_update_user_role(user_id):
    data = request.get_json()
    user = User.query.get_or_404(user_id)
    new_role = data.get('role')
    if new_role in ['customer', 'partner', 'admin']:
        user.role = new_role
        db.session.commit()
    return jsonify({'success': True})


@app.route('/oriflame-admin-panel-x9k2/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def admin_toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    status = 'activated' if user.is_active else 'deactivated'
    return jsonify({'success': True, 'message': f'User {status}'})


@app.route('/oriflame-admin-panel-x9k2/mlm', methods=['GET'])
@login_required
@admin_required
def admin_mlm():
    partners = User.query.filter_by(role='partner').all()
    total_commissions = db.session.query(db.func.sum(MLMCommission.amount)).scalar() or 0
    total_network_sales = db.session.query(db.func.sum(User.total_sales)).filter_by(role='partner').scalar() or 0
    pending_commissions = MLMCommission.query.filter_by(status='pending').count()
    commissions = MLMCommission.query.order_by(MLMCommission.created_at.desc()).limit(20).all()
    
    return render_template('admin/mlm.html',
                           partners=partners,
                           total_commissions=total_commissions,
                           total_network_sales=total_network_sales,
                           pending_commissions=pending_commissions,
                           commissions=commissions)


@app.route('/oriflame-admin-panel-x9k2/blog', methods=['GET'])
@login_required
@admin_required
def admin_blog():
    posts = BlogPost.query.order_by(BlogPost.created_at.desc()).all()
    return render_template('admin/blog.html', posts=posts)


@app.route('/oriflame-admin-panel-x9k2/blog', methods=['POST'])
@login_required
@admin_required
def admin_save_blog():
    form = request.form
    post_id = form.get('id')

    if post_id:
        post = BlogPost.query.get_or_404(int(post_id))
    else:
        post = BlogPost()
        db.session.add(post)

    post.title = form.get('title', 'Untitled')
    post.slug = slugify(post.title) or uuid.uuid4().hex[:10]
    post.summary = form.get('summary', '')
    post.content = form.get('content', '')
    post.is_active = bool(form.get('is_active'))

    # Handle Cover Image Upload
    cover_file = request.files.get('cover_file')
    if cover_file and cover_file.filename:
        filename = secure_filename(cover_file.filename)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        unique_filename = f"blog_{timestamp}_{filename}"
        dir_path = os.path.join(BASE_DIR, 'static', 'images', 'uploads')
        filepath = os.path.join(dir_path, unique_filename)
        cover_file.save(filepath)
        post.cover_image = f"/static/images/uploads/{unique_filename}"
    else:
        cover_url = form.get('cover_image', '').strip()
        if cover_url:
            post.cover_image = cover_url

    # Check slug uniqueness
    existing = BlogPost.query.filter(BlogPost.slug == post.slug, BlogPost.id != post.id).first()
    if existing:
        post.slug = f"{post.slug}-{uuid.uuid4().hex[:6]}"

    try:
        db.session.commit()
        return jsonify({'success': True, 'message': 'Blog post saved successfully!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@app.route('/oriflame-admin-panel-x9k2/blog/<int:post_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_blog(post_id):
    post = BlogPost.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Blog post deleted!'})


@app.route('/oriflame-admin-panel-x9k2/blog/<int:post_id>/toggle', methods=['POST'])
@login_required
@admin_required
def admin_toggle_blog(post_id):
    post = BlogPost.query.get_or_404(post_id)
    post.is_active = not post.is_active
    db.session.commit()
    status = 'published' if post.is_active else 'hidden'
    return jsonify({'success': True, 'message': f'Post is now {status}!', 'is_active': post.is_active})




def slugify(text):
    """Create a URL-friendly slug from text."""
    import re
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text).strip('-')
    return text


# ═══════════════════════════════════════════════════════════════════════════════
#  ERROR HANDLERS
# ═══════════════════════════════════════════════════════════════════════════════

@app.errorhandler(404)
def not_found(e):
    return render_template('base.html', content='<div class="empty-state"><div class="empty-state-icon">404</div><h3>Page Not Found</h3><p>The page you\'re looking for doesn\'t exist.</p><a href="/" class="btn btn-primary">Go Home</a></div>'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('base.html', content='<div class="empty-state"><div class="empty-state-icon">500</div><h3>Server Error</h3><p>Something went wrong.</p></div>'), 500


# ═══════════════════════════════════════════════════════════════════════════════
#  DATABASE INITIALIZATION & SEED
# ═══════════════════════════════════════════════════════════════════════════════

def seed_database():
    """Seed the database with initial data."""
    # Check if already seeded
    if User.query.first():
        return
    
    print("[SEED] Seeding database...")
    
    # Create admin user
    admin = User(
        email='admin@oriflame.com',
        first_name='Admin',
        last_name='Oriflame',
        phone='+91 9876543210',
        role='admin'
    )
    admin.set_password('admin123')
    db.session.add(admin)
    
    # Create sample partner
    partner1 = User(
        email='partner@oriflame.com',
        first_name='Priya',
        last_name='Sharma',
        phone='+91 9876543211',
        role='partner'
    )
    partner1.set_password('partner123')
    db.session.add(partner1)
    
    partner2 = User(
        email='partner2@oriflame.com',
        first_name='Rahul',
        last_name='Verma',
        phone='+91 9876543212',
        role='partner',
        sponsor_id=None  # Will set after flush
    )
    partner2.set_password('partner123')
    db.session.add(partner2)
    
    # Create sample customer
    customer = User(
        email='customer@oriflame.com',
        first_name='Anita',
        last_name='Patel',
        phone='+91 9876543213',
        role='customer'
    )
    customer.set_password('customer123')
    db.session.add(customer)
    
    db.session.flush()
    
    # Set sponsor relationships
    partner2.sponsor_id = partner1.id
    
    # Create categories
    categories_data = [
        {'name': 'Skincare', 'slug': 'skincare', 'icon': '🧴', 'order': 1},
        {'name': 'Makeup', 'slug': 'makeup', 'icon': '💄', 'order': 2},
        {'name': 'Fragrance', 'slug': 'fragrance', 'icon': '🌸', 'order': 3},
        {'name': 'Hair Care', 'slug': 'hair-care', 'icon': '💇', 'order': 4},
        {'name': 'Bath & Body', 'slug': 'bath-and-body', 'icon': '🛁', 'order': 5},
        {'name': 'Personal Care', 'slug': 'personal-care', 'icon': '🪥', 'order': 6},
        {'name': 'Wellness', 'slug': 'wellness', 'icon': '🌿', 'order': 7},
        {'name': 'Accessories', 'slug': 'accessories', 'icon': '👜', 'order': 8},
        {'name': 'Men\'s Care', 'slug': 'mens-care', 'icon': '🧔', 'order': 9},
        {'name': 'Gift Sets', 'slug': 'gift-sets', 'icon': '🎁', 'order': 10},
    ]
    
    cats = {}
    for cd in categories_data:
        cat = Category(
            name=cd['name'],
            slug=cd['slug'],
            icon=cd['icon'],
            display_order=cd['order'],
            description=f"Explore our {cd['name'].lower()} collection"
        )
        db.session.add(cat)
        cats[cd['slug']] = cat
    
    db.session.flush()
    
    # Create products
    products_data = [
        # Skincare
        {'name': 'NovAge Ultimate Lift Day Cream SPF 15', 'code': '41048', 'price': 2499, 'mrp': 3999, 'cat': 'skincare', 'brand': 'NovAge', 'weight': '50ml', 'new': True, 'best': True, 'feat': True, 'rating': 4.5, 'reviews': 342},
        {'name': 'Optimals Hydra Radiance Day Cream', 'code': '42510', 'price': 699, 'mrp': 999, 'cat': 'skincare', 'brand': 'Optimals', 'weight': '50ml', 'new': False, 'best': True, 'feat': False, 'rating': 4.3, 'reviews': 218},
        {'name': 'Essentials Fairness 5-in-1 Face Cream', 'code': '42511', 'price': 449, 'mrp': 599, 'cat': 'skincare', 'brand': 'Essentials', 'weight': '75ml', 'new': False, 'best': True, 'feat': False, 'rating': 4.2, 'reviews': 567},
        {'name': 'NovAge Bright Sublime Serum', 'code': '42512', 'price': 1899, 'mrp': 2999, 'cat': 'skincare', 'brand': 'NovAge', 'weight': '30ml', 'new': True, 'best': False, 'feat': True, 'rating': 4.7, 'reviews': 89},
        {'name': 'Love Nature Tea Tree Face Wash', 'code': '42513', 'price': 349, 'mrp': 449, 'cat': 'skincare', 'brand': 'Love Nature', 'weight': '125ml', 'new': False, 'best': True, 'feat': False, 'rating': 4.4, 'reviews': 890},
        {'name': 'Optimals Even Out Night Cream', 'code': '42514', 'price': 799, 'mrp': 1099, 'cat': 'skincare', 'brand': 'Optimals', 'weight': '50ml', 'new': True, 'best': False, 'feat': False, 'rating': 4.1, 'reviews': 156},
        
        # Fragrance
        {'name': 'Love Potion Cherry on Top Eau de Parfum', 'code': '46047', 'price': 2939, 'mrp': 4899, 'cat': 'fragrance', 'brand': 'Love Potion', 'weight': '50ml', 'new': True, 'best': True, 'feat': True, 'rating': 4.8, 'reviews': 1637},
        {'name': 'Eclat Femme Weekend Riviera EDT', 'code': '46792', 'price': 2229, 'mrp': 3699, 'cat': 'fragrance', 'brand': 'Eclat', 'weight': '50ml', 'new': True, 'best': False, 'feat': True, 'rating': 4.6, 'reviews': 838},
        {'name': 'Giordani Gold Essenza Parfum', 'code': '42601', 'price': 3499, 'mrp': 5999, 'cat': 'fragrance', 'brand': 'Giordani Gold', 'weight': '50ml', 'new': False, 'best': True, 'feat': True, 'rating': 4.9, 'reviews': 2100},
        {'name': 'Possess Eau de Parfum', 'code': '42602', 'price': 1899, 'mrp': 2999, 'cat': 'fragrance', 'brand': 'Possess', 'weight': '50ml', 'new': False, 'best': True, 'feat': False, 'rating': 4.5, 'reviews': 1200},
        {'name': 'All or Nothing Amplified EDP', 'code': '42603', 'price': 2199, 'mrp': 3499, 'cat': 'fragrance', 'brand': 'All or Nothing', 'weight': '50ml', 'new': True, 'best': False, 'feat': False, 'rating': 4.4, 'reviews': 450},
        
        # Makeup
        {'name': 'The ONE Illuskin Aqua Foundation', 'code': '43001', 'price': 899, 'mrp': 1299, 'cat': 'makeup', 'brand': 'The ONE', 'weight': '30ml', 'new': False, 'best': True, 'feat': True, 'rating': 4.3, 'reviews': 780},
        {'name': 'Giordani Gold Mastercreation Lipstick', 'code': '43002', 'price': 1299, 'mrp': 1999, 'cat': 'makeup', 'brand': 'Giordani Gold', 'weight': '4g', 'new': True, 'best': True, 'feat': True, 'rating': 4.7, 'reviews': 560},
        {'name': 'The ONE Power Shine Lip Gloss', 'code': '43003', 'price': 599, 'mrp': 849, 'cat': 'makeup', 'brand': 'The ONE', 'weight': '8ml', 'new': True, 'best': False, 'feat': False, 'rating': 4.2, 'reviews': 320},
        {'name': 'Very Me Clickit Eyeliner', 'code': '43004', 'price': 399, 'mrp': 549, 'cat': 'makeup', 'brand': 'Very Me', 'weight': '3ml', 'new': False, 'best': True, 'feat': False, 'rating': 4.5, 'reviews': 910},
        {'name': 'OnColour Perfecting Primer', 'code': '43005', 'price': 499, 'mrp': 699, 'cat': 'makeup', 'brand': 'OnColour', 'weight': '30ml', 'new': False, 'best': False, 'feat': True, 'rating': 4.1, 'reviews': 230},
        {'name': 'The ONE High Impact Mascara', 'code': '43006', 'price': 749, 'mrp': 1099, 'cat': 'makeup', 'brand': 'The ONE', 'weight': '8ml', 'new': True, 'best': True, 'feat': False, 'rating': 4.6, 'reviews': 670},
        
        # Hair Care
        {'name': 'HairX Advanced Care Deep Repair Shampoo', 'code': '44001', 'price': 549, 'mrp': 799, 'cat': 'hair-care', 'brand': 'HairX', 'weight': '250ml', 'new': False, 'best': True, 'feat': False, 'rating': 4.3, 'reviews': 450},
        {'name': 'Love Nature Wheat & Coconut Oil Shampoo', 'code': '44002', 'price': 349, 'mrp': 449, 'cat': 'hair-care', 'brand': 'Love Nature', 'weight': '250ml', 'new': True, 'best': False, 'feat': False, 'rating': 4.2, 'reviews': 310},
        {'name': 'HairX TruColour Conditioner', 'code': '44003', 'price': 599, 'mrp': 849, 'cat': 'hair-care', 'brand': 'HairX', 'weight': '250ml', 'new': False, 'best': False, 'feat': True, 'rating': 4.1, 'reviews': 190},
        
        # Bath & Body
        {'name': 'Love Nature Shower Gel Organic Mango', 'code': '46987', 'price': 279, 'mrp': 329, 'cat': 'bath-and-body', 'brand': 'Love Nature', 'weight': '250ml', 'new': True, 'best': False, 'feat': False, 'rating': 4.4, 'reviews': 1140},
        {'name': 'Love Potion Sensual Ruby Body Cream', 'code': '47019', 'price': 899, 'mrp': 1299, 'cat': 'bath-and-body', 'brand': 'Love Potion', 'weight': '250ml', 'new': True, 'best': True, 'feat': False, 'rating': 4.5, 'reviews': 601},
        {'name': 'Tender Care Watermelon Balm', 'code': '49133', 'price': 229, 'mrp': 459, 'cat': 'bath-and-body', 'brand': 'Tender Care', 'weight': '15ml', 'new': True, 'best': True, 'feat': True, 'rating': 4.6, 'reviews': 357},
        {'name': 'Love Potion Cherry On Top Hand Cream', 'code': '46979', 'price': 285, 'mrp': 469, 'cat': 'bath-and-body', 'brand': 'Love Potion', 'weight': '75ml', 'new': True, 'best': False, 'feat': False, 'rating': 4.3, 'reviews': 1266},
        {'name': 'Sweet Delights Shower Cream Pumpkin & Cinnamon', 'code': '47273', 'price': 399, 'mrp': 499, 'cat': 'bath-and-body', 'brand': 'Love Nature', 'weight': '200ml', 'new': True, 'best': False, 'feat': False, 'rating': 4.2, 'reviews': 632},
        
        # Personal Care
        {'name': 'Optifresh Kids Strawberry Toothpaste', 'code': '48312', 'price': 95, 'mrp': 129, 'cat': 'personal-care', 'brand': 'Optifresh', 'weight': '50g', 'new': True, 'best': False, 'feat': False, 'rating': 4.0, 'reviews': 3},
        {'name': 'Optifresh Maximum Fresh Toothpaste', 'code': '48310', 'price': 135, 'mrp': 179, 'cat': 'personal-care', 'brand': 'Optifresh', 'weight': '100g', 'new': True, 'best': False, 'feat': False, 'rating': 4.1, 'reviews': 2},
        {'name': 'Optifresh Kids Toothbrush Soft', 'code': '49135', 'price': 99, 'mrp': 129, 'cat': 'personal-care', 'brand': 'Optifresh', 'weight': '1pc', 'new': True, 'best': False, 'feat': False, 'rating': 4.0, 'reviews': 57},
        {'name': 'Activelle Anti-Perspirant Roll-On', 'code': '42801', 'price': 299, 'mrp': 399, 'cat': 'personal-care', 'brand': 'Activelle', 'weight': '50ml', 'new': False, 'best': True, 'feat': False, 'rating': 4.4, 'reviews': 890},
        
        # Wellness
        {'name': 'Wellness Pack Omega-3', 'code': '45001', 'price': 1499, 'mrp': 1999, 'cat': 'wellness', 'brand': 'Wellness', 'weight': '60 capsules', 'new': False, 'best': True, 'feat': True, 'rating': 4.5, 'reviews': 340},
        {'name': 'NutriShake Chocolate', 'code': '45002', 'price': 1299, 'mrp': 1799, 'cat': 'wellness', 'brand': 'Wellness', 'weight': '500g', 'new': True, 'best': False, 'feat': False, 'rating': 4.3, 'reviews': 220},
        {'name': 'Swedish Beauty Complex Plus', 'code': '45003', 'price': 999, 'mrp': 1499, 'cat': 'wellness', 'brand': 'Wellness', 'weight': '60 tablets', 'new': False, 'best': False, 'feat': True, 'rating': 4.6, 'reviews': 180},
        
        # Accessories
        {'name': 'Giordani Gold Makeup Pouch', 'code': '46001', 'price': 799, 'mrp': 999, 'cat': 'accessories', 'brand': 'Giordani Gold', 'weight': '1pc', 'new': True, 'best': False, 'feat': True, 'rating': 4.2, 'reviews': 120},
        {'name': 'Crystal Encrusted Compact Mirror', 'code': '46002', 'price': 599, 'mrp': 799, 'cat': 'accessories', 'brand': 'Oriflame', 'weight': '1pc', 'new': False, 'best': True, 'feat': False, 'rating': 4.4, 'reviews': 310},
        
        # Men's Care
        {'name': 'North For Men Active Shower Gel', 'code': '47001', 'price': 499, 'mrp': 699, 'cat': 'mens-care', 'brand': 'North For Men', 'weight': '250ml', 'new': False, 'best': True, 'feat': True, 'rating': 4.5, 'reviews': 520},
        {'name': 'NovAge Men Energising Face Cream', 'code': '47002', 'price': 1299, 'mrp': 1899, 'cat': 'mens-care', 'brand': 'NovAge Men', 'weight': '50ml', 'new': True, 'best': False, 'feat': False, 'rating': 4.3, 'reviews': 190},
        {'name': 'North For Men Intense EDT', 'code': '47003', 'price': 1699, 'mrp': 2499, 'cat': 'mens-care', 'brand': 'North For Men', 'weight': '75ml', 'new': False, 'best': True, 'feat': True, 'rating': 4.7, 'reviews': 890},
        
        # Gift Sets
        {'name': 'Love Potion Valentine Gift Set', 'code': '48001', 'price': 2999, 'mrp': 4499, 'cat': 'gift-sets', 'brand': 'Love Potion', 'weight': 'Set', 'new': True, 'best': True, 'feat': True, 'rating': 4.8, 'reviews': 410},
        {'name': 'Giordani Gold Luxury Gift Collection', 'code': '48002', 'price': 4999, 'mrp': 7499, 'cat': 'gift-sets', 'brand': 'Giordani Gold', 'weight': 'Set', 'new': False, 'best': True, 'feat': True, 'rating': 4.9, 'reviews': 280},
        {'name': 'Essentials Beauty Starter Kit', 'code': '48003', 'price': 999, 'mrp': 1499, 'cat': 'gift-sets', 'brand': 'Essentials', 'weight': 'Set', 'new': True, 'best': False, 'feat': False, 'rating': 4.2, 'reviews': 150},
    ]
    
    for pd_item in products_data:
        product = Product(
            name=pd_item['name'],
            code=pd_item['code'],
            slug=slugify(pd_item['name']),
            price=pd_item['price'],
            mrp=pd_item['mrp'],
            category_id=cats[pd_item['cat']].id,
            brand=pd_item['brand'],
            weight=pd_item['weight'],
            is_new=pd_item['new'],
            is_bestseller=pd_item['best'],
            is_featured=pd_item['feat'],
            rating=pd_item['rating'],
            review_count=pd_item['reviews'],
            stock=100,
            short_description=f"Premium {pd_item['brand']} {pd_item['name'].split()[-1].lower()} crafted with Swedish beauty innovation.",
            description=f"Discover the {pd_item['name']} from {pd_item['brand']}. This premium product is designed to deliver exceptional results with carefully selected ingredients and Swedish beauty expertise. Experience the Oriflame difference with this must-have addition to your beauty routine.",
            image_url=f'/static/images/products/{pd_item["code"]}.png'
        )
        db.session.add(product)
    
    db.session.commit()
    print(f"[OK] Seeded {len(products_data)} products, {len(categories_data)} categories, 4 users")


# ─── Self-Healing Database (Run on every start) ───────────────────────────────
with app.app_context():
    try:
        db.create_all()
        # Seed if empty
        if User.query.count() == 0:
            print("[SEED] No users found. Seeding initial data...")
            seed_database()
            
        # Sync PostgreSQL sequences
        if db.engine.name == 'postgresql':
            tables = ['users', 'categories', 'products', 'product_images', 'catalogues', 'carts', 'cart_items', 'addresses', 'orders', 'order_items', 'transactions', 'mlm_commissions', 'wishlists', 'blog_posts', 'contact_messages', 'reviews']
            for table in tables:
                max_id = db.session.execute(db.text(f"SELECT MAX(id) FROM {table}")).scalar()
                if max_id is not None:
                    db.session.execute(db.text(f"SELECT setval('{table}_id_seq', {max_id})"))
            db.session.commit()
            print("[DB] Synced PostgreSQL sequences successfully.", flush=True)
    except Exception as e:
        print(f"[DB ERROR] Startup check failed: {e}. Attempting to proceed anyway...", flush=True)
        db.session.rollback()

# ─── Main Entry ───────────────────────────────────────────────────────────────
@app.route('/oriflame-admin-panel-x9k2/fix_orphans', methods=['GET', 'POST'])
@login_required
def fix_orphans():
    if not current_user.is_admin:
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    
    all_products = Product.query.all()
    count = 0
    
    # Simple grouping logic: Find products with identical or very similar names
    # and set the first one as the parent of the others.
    processed = set()
    
    for p in all_products:
        if p.id in processed:
            continue
            
        # Get first 3 words for matching
        name_parts = p.name.strip().split()
        if len(name_parts) < 2:
            continue
            
        base_name = " ".join(name_parts[:3]) if len(name_parts) >= 3 else " ".join(name_parts[:2])
        
        # Find all similar products that are orphans
        similar = Product.query.filter(
            Product.name.ilike(f"{base_name}%"),
            Product.parent_id == None,
            Product.id != p.id
        ).all()
        
        if similar:
            for s in similar:
                s.parent_id = p.id
                processed.add(s.id)
                count += 1
            processed.add(p.id)
            
    db.session.commit()
    return jsonify({"success": True, "message": f"Successfully linked {count} orphan variants!"})

@app.route('/oriflame-admin-panel-x9k2/get_product/<int:product_id>')
@login_required
def get_product_data(product_id):
    if not current_user.is_admin:
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    p = Product.query.get_or_404(product_id)
    return jsonify({
        "success": True,
        "id": p.id,
        "name": p.name,
        "code": p.code,
        "price": p.price,
        "mrp": p.mrp,
        "stock": p.stock,
        "category_id": p.category_id,
        "brand": p.brand,
        "weight": p.weight,
        "shade_name": p.shade_name,
        "shade_color": p.shade_color,
        "shade_color_2": p.shade_color_2,
        "short_description": p.short_description,
        "description": p.description,
        "how_to_use": p.how_to_use,
        "ingredients": p.ingredients,
        "image_url": p.image_url,
        "parent_id": p.parent_id,
        "is_new": p.is_new,
        "is_bestseller": p.is_bestseller
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_database()
    
    app.run(debug=True, port=5000)
