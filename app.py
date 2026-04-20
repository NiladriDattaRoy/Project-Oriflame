"""
Oriflame E-Commerce & MLM Platform — Main Application
Flask application with all routes for the public store, user dashboard, and admin panel.
"""
import json
import os
import uuid
from datetime import datetime
from functools import wraps

from sqlalchemy import inspect, text

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, jsonify, abort
)
from flask_login import (
    LoginManager, login_user, logout_user, login_required, current_user
)

from config import Config, BASE_DIR
from models import (
    db, User, Category, Product, Cart, CartItem,
    Address, Order, OrderItem, Transaction, MLMCommission, Wishlist
)

# ─── App Factory ──────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config.from_object(Config)

# Ensure database directory exists
os.makedirs(os.path.join(BASE_DIR, 'database'), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, 'static', 'images', 'uploads'), exist_ok=True)

db.init_app(app)

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
    if current_user.is_authenticated and current_user.cart:
        cart_count = current_user.cart.item_count
    return dict(categories=categories, cart_count=cart_count)


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
    buyer = order.user
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


def ensure_db_schema():
    """Apply lightweight SQLite migrations for new columns."""
    try:
        inspector = inspect(db.engine)
        cols = {c['name'] for c in inspector.get_columns('orders')}
        if 'razorpay_order_id' not in cols:
            with db.engine.begin() as conn:
                conn.execute(text('ALTER TABLE orders ADD COLUMN razorpay_order_id VARCHAR(100)'))
    except Exception as exc:
        print(f"[WARN] ensure_db_schema: {exc}")


def get_razorpay_client():
    """Return Razorpay client if configured, else None."""
    if not app.config.get('RAZORPAY_ENABLED'):
        return None
    try:
        import razorpay
        return razorpay.Client(auth=(
            app.config['RAZORPAY_KEY_ID'],
            app.config['RAZORPAY_KEY_SECRET'],
        ))
    except Exception as exc:
        print(f"[WARN] Razorpay client: {exc}")
        return None


def finalize_successful_payment(order, *, transaction_ref, method_override=None, gateway_payload=None):
    """
    Mark order paid, record transaction, update buyer sales, run MLM commissions.
    Idempotent if already paid or transaction_ref already recorded.
    """
    if order.payment_status == 'paid':
        return {
            'success': True,
            'order_number': order.order_number,
            'transaction_ref': transaction_ref,
            'already_paid': True,
        }

    if Transaction.query.filter_by(transaction_ref=transaction_ref).first():
        return {
            'success': True,
            'order_number': order.order_number,
            'transaction_ref': transaction_ref,
            'already_paid': True,
        }

    buyer = User.query.get(order.user_id)
    if not buyer:
        return {'success': False, 'message': 'Buyer not found'}

    method = method_override or order.payment_method or 'unknown'
    txn = Transaction(
        order_id=order.id,
        transaction_ref=transaction_ref[:100],
        amount=order.total,
        method=method,
        status='success',
        gateway_response=json.dumps(gateway_payload) if gateway_payload else None,
    )
    db.session.add(txn)

    order.status = 'confirmed'
    order.payment_status = 'paid'
    buyer.total_sales += order.total

    calculate_mlm_commissions(order)

    return {
        'success': True,
        'order_number': order.order_number,
        'transaction_ref': transaction_ref,
    }


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
    
    # Search
    search = request.args.get('search', '').strip()
    if search:
        query = query.filter(
            (Product.name.ilike(f'%{search}%')) |
            (Product.brand.ilike(f'%{search}%')) |
            (Product.tags.ilike(f'%{search}%'))
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
    
    # Sort
    sort = request.args.get('sort', 'newest')
    if sort == 'price_low':
        query = query.order_by(Product.price.asc())
    elif sort == 'price_high':
        query = query.order_by(Product.price.desc())
    elif sort == 'rating':
        query = query.order_by(Product.rating.desc())
    elif sort == 'popular':
        query = query.order_by(Product.review_count.desc())
    else:
        query = query.order_by(Product.created_at.desc())
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = Config.PRODUCTS_PER_PAGE
    total = query.count()
    total_pages = (total + per_page - 1) // per_page
    products_list = query.offset((page - 1) * per_page).limit(per_page).all()
    
    return render_template('products.html',
                           products=products_list,
                           page=page,
                           total_pages=total_pages,
                           category=None)


@app.route('/category/<slug>')
def category_page(slug):
    category = Category.query.filter_by(slug=slug, is_active=True).first_or_404()
    
    query = Product.query.filter_by(category_id=category.id, is_active=True)
    
    sort = request.args.get('sort', 'newest')
    if sort == 'price_low':
        query = query.order_by(Product.price.asc())
    elif sort == 'price_high':
        query = query.order_by(Product.price.desc())
    elif sort == 'rating':
        query = query.order_by(Product.rating.desc())
    else:
        query = query.order_by(Product.created_at.desc())
    
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
    related = Product.query.filter(
        Product.category_id == product.category_id,
        Product.id != product.id,
        Product.is_active == True
    ).limit(4).all()
    
    return render_template('product_detail.html', product=product, related_products=related)


@app.route('/join')
def join_page():
    return render_template('join.html')


@app.route('/search')
def search_page():
    return redirect(url_for('products', search=request.args.get('q', '')))


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
        payment_method = request.form.get('payment_method', 'cod')

        if payment_method in ('card', 'upi') and not app.config.get('RAZORPAY_ENABLED'):
            return jsonify({
                'success': False,
                'message': (
                    'Online payments are not configured. Set environment variables '
                    'RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET (Razorpay test or live keys), '
                    'or choose Cash on delivery.'
                ),
            }), 400

        shipping_fee = 0 if cart_total >= 999 else 99
        order = Order(
            order_number=generate_order_number(),
            user_id=current_user.id,
            subtotal=cart_total,
            shipping_fee=shipping_fee,
            total=cart_total + shipping_fee,
            payment_method=payment_method,
            shipping_name=request.form.get('shipping_name'),
            shipping_phone=request.form.get('shipping_phone'),
            shipping_address=request.form.get('shipping_address'),
            shipping_city=request.form.get('shipping_city'),
            shipping_state=request.form.get('shipping_state'),
            shipping_pincode=request.form.get('shipping_pincode'),
            notes=request.form.get('notes'),
        )

        try:
            db.session.add(order)
            db.session.flush()

            for item in cart_items:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=item.product_id,
                    product_name=item.product.name,
                    product_image=item.product.image_url,
                    quantity=item.quantity,
                    price=item.product.price,
                    mrp=item.product.mrp,
                )
                db.session.add(order_item)
                item.product.stock -= item.quantity

            razorpay_payload = None
            if payment_method in ('card', 'upi'):
                client = get_razorpay_client()
                if not client:
                    db.session.rollback()
                    return jsonify({
                        'success': False,
                        'message': 'Razorpay client could not be initialized.',
                    }), 503
                amount_paise = int(round(order.total * 100))
                receipt = (order.order_number or 'order')[:40]
                rp_order = client.order.create({
                    'amount': amount_paise,
                    'currency': 'INR',
                    'receipt': receipt,
                    'payment_capture': 1,
                    'notes': {'internal_order_id': str(order.id)},
                })
                order.razorpay_order_id = rp_order['id']
                razorpay_payload = {
                    'key_id': app.config['RAZORPAY_KEY_ID'],
                    'order_id': rp_order['id'],
                    'amount': rp_order.get('amount', amount_paise),
                    'currency': rp_order.get('currency', 'INR'),
                }

            if request.form.get('shipping_name'):
                existing_addr = Address.query.filter_by(
                    user_id=current_user.id,
                    pincode=request.form.get('shipping_pincode'),
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
                        is_default=len(addresses) == 0,
                    )
                    db.session.add(addr)

            for item in list(cart_items):
                db.session.delete(item)

            db.session.commit()
        except Exception as exc:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': f'Could not create order or payment session: {exc}',
            }), 502

        out = {
            'success': True,
            'order_id': order.id,
            'order_number': order.order_number,
        }
        if razorpay_payload:
            out['razorpay'] = razorpay_payload
        return jsonify(out)
    
    return render_template(
        'checkout.html',
        cart_items=cart_items,
        cart_total=cart_total,
        addresses=addresses,
        razorpay_enabled=app.config.get('RAZORPAY_ENABLED', False),
        razorpay_key_id=app.config.get('RAZORPAY_KEY_ID', ''),
    )


@app.route('/payment/process', methods=['POST'])
@login_required
def process_payment():
    """Complete simulated payment (COD, wallet) — not used for Razorpay card/UPI orders."""
    data = request.get_json()
    order_id = data.get('order_id')

    order = Order.query.get(order_id)
    if not order or order.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Order not found'}), 404

    if order.razorpay_order_id:
        return jsonify({
            'success': False,
            'message': 'This order is paid online. Complete payment in the Razorpay window.',
        }), 400

    if order.payment_status == 'paid':
        last_txn = (
            Transaction.query.filter_by(order_id=order.id)
            .order_by(Transaction.created_at.desc())
            .first()
        )
        ref = last_txn.transaction_ref if last_txn else generate_transaction_ref()
        return jsonify({
            'success': True,
            'order_number': order.order_number,
            'transaction_ref': ref,
        })

    ref = generate_transaction_ref()
    result = finalize_successful_payment(
        order,
        transaction_ref=ref,
        gateway_payload={'mode': 'simulated', 'method': order.payment_method},
    )
    if not result.get('success'):
        return jsonify(result), 400
    return jsonify({
        'success': True,
        'order_number': result['order_number'],
        'transaction_ref': result['transaction_ref'],
    })


@app.route('/payment/razorpay/verify', methods=['POST'])
@login_required
def razorpay_verify_payment():
    """
    Verify Razorpay payment signature and finalize the order.
    See https://razorpay.com/docs/payments/server-integration/python/payment-verification/
    """
    data = request.get_json() or {}
    order = Order.query.get(data.get('order_id'))
    if not order or order.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Order not found'}), 404

    if not order.razorpay_order_id:
        return jsonify({'success': False, 'message': 'This order is not awaiting an online payment.'}), 400

    razorpay_order_id = data.get('razorpay_order_id', '')
    razorpay_payment_id = data.get('razorpay_payment_id', '')
    razorpay_signature = data.get('razorpay_signature', '')

    if razorpay_order_id != order.razorpay_order_id:
        return jsonify({'success': False, 'message': 'Payment does not match this order.'}), 400

    client = get_razorpay_client()
    if not client:
        return jsonify({'success': False, 'message': 'Payment gateway is not configured.'}), 503

    params_dict = {
        'razorpay_order_id': razorpay_order_id,
        'razorpay_payment_id': razorpay_payment_id,
        'razorpay_signature': razorpay_signature,
    }
    try:
        client.utility.verify_payment_signature(params_dict)
    except Exception:
        return jsonify({'success': False, 'message': 'Payment verification failed. If money was debited, contact support with your payment ID.'}), 400

    result = finalize_successful_payment(
        order,
        transaction_ref=razorpay_payment_id,
        gateway_payload={'razorpay': params_dict},
    )
    if not result.get('success'):
        return jsonify(result), 400
    return jsonify({
        'success': True,
        'order_number': result['order_number'],
        'transaction_ref': result['transaction_ref'],
    })


# ═══════════════════════════════════════════════════════════════════════════════
#  USER DASHBOARD ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/dashboard')
@login_required
def dashboard():
    order_count = Order.query.filter_by(user_id=current_user.id).count()
    total_spent = db.session.query(db.func.sum(Order.total)).filter_by(
        user_id=current_user.id, payment_status='paid'
    ).scalar() or 0
    
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

@app.route('/oriflame-admin-panel-x9k2/')
@login_required
@admin_required
def admin_dashboard():
    total_revenue = db.session.query(db.func.sum(Order.total)).filter_by(payment_status='paid').scalar() or 0
    total_orders = Order.query.count()
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
    products_list = Product.query.order_by(Product.created_at.desc()).all()
    categories_list = Category.query.all()
    return render_template('admin/products.html', products=products_list, categories=categories_list)


@app.route('/oriflame-admin-panel-x9k2/products', methods=['POST'])
@app.route('/oriflame-admin-panel-x9k2/products/<int:product_id>', methods=['POST'])
@login_required
@admin_required
def admin_save_product(product_id=None):
    form = request.form
    
    if product_id:
        product = Product.query.get_or_404(product_id)
    else:
        product = Product()
        db.session.add(product)
    
    product.name = form.get('name')
    product.code = form.get('code')
    product.slug = slugify(form.get('name'))
    product.price = float(form.get('price', 0))
    product.mrp = float(form.get('mrp', 0))
    product.category_id = int(form.get('category_id'))
    product.stock = int(form.get('stock', 100))
    product.brand = form.get('brand')
    product.weight = form.get('weight')
    product.description = form.get('description')
    product.image_url = form.get('image_url')
    product.is_new = bool(form.get('is_new'))
    product.is_bestseller = bool(form.get('is_bestseller'))
    product.is_active = True
    
    # Ensure unique slug
    existing = Product.query.filter(Product.slug == product.slug, Product.id != product.id).first()
    if existing:
        product.slug = product.slug + '-' + product.code.lower()
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Product saved successfully!'})


@app.route('/oriflame-admin-panel-x9k2/products/<int:product_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    product.is_active = False  # Soft delete
    db.session.commit()
    return jsonify({'success': True, 'message': 'Product deleted!'})


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
    order.status = data.get('status', order.status)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/oriflame-admin-panel-x9k2/users', methods=['GET'])
@login_required
@admin_required
def admin_users():
    users_list = User.query.order_by(User.join_date.desc()).all()
    return render_template('admin/users.html', users=users_list)


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


# ─── Main Entry ───────────────────────────────────────────────────────────────
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        ensure_db_schema()
        seed_database()
    
    app.run(debug=True, port=5000)
