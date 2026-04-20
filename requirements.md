# Oriflame E-Commerce & MLM Platform — Requirements

## Project Overview
A full-stack e-commerce and direct-selling (multi-level marketing) platform inspired by [Oriflame India](https://in.oriflame.com/). The platform enables customers to browse and purchase beauty products, while Brand Partners can earn commissions through a 3-level MLM network.

---

## System Requirements

### Software Dependencies
| Software | Version |
|----------|---------|
| Python | 3.9+ |
| pip | Latest |
| Modern Browser | Chrome, Firefox, Edge, Safari |

### Python Packages
| Package | Version | Purpose |
|---------|---------|---------|
| Flask | 3.1.1 | Web framework |
| Flask-SQLAlchemy | 3.1.1 | Database ORM |
| Flask-Login | 0.6.3 | User authentication |
| Flask-WTF | 1.2.2 | Form handling & CSRF |
| Werkzeug | 3.1.3 | Password hashing & utilities |
| bcrypt | 4.3.0 | Password encryption |
| Pillow | 11.2.1 | Image processing |

---

## Installation & Setup

### Step 1: Clone / Extract
```bash
# Extract the ZIP file or navigate to the project directory
cd Oriflame
```

### Step 2: Create Virtual Environment (Recommended)
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Run the Application
```bash
python app.py
```

The application will:
1. Create the SQLite database automatically
2. Seed it with 40+ products, 10 categories, and sample users
3. Start the server at `http://localhost:5000`

---

## User Accounts

### Default Admin Account
- **URL**: `http://localhost:5000/oriflame-admin-panel-x9k2/`
- **Email**: `admin@oriflame.com`
- **Password**: `admin123`

### Sample Brand Partner
- **Email**: `partner@oriflame.com`
- **Password**: `partner123`

### Sample Customer
- **Email**: `customer@oriflame.com`
- **Password**: `customer123`

---

## Features

### Public Storefront
- Homepage with hero carousel, product tabs, category showcase
- Product listing with filters (category, price, rating), sorting, and search
- Product detail pages with gallery, pricing, and related products
- Shopping cart (sidebar + full page) with quantity management
- Checkout with address form and multiple payment methods
- User registration (Customer or Brand Partner)
- Responsive design for all devices

### User Dashboard
- Order history with status tracking
- Profile management
- Wishlist management
- MLM network tree visualization (Brand Partners)
- Commission history with level filters

### Admin Panel (Hidden)
- Accessible only at `/oriflame-admin-panel-x9k2/`
- Not linked from any public page
- Returns 404 for non-admin users
- Dashboard with revenue, orders, users analytics
- Product CRUD (Add, Edit, Delete)
- Order management with status updates
- User management with role assignment
- MLM network overview and commission tracking

### Payment System (Simulated)
- Credit/Debit Card
- UPI
- Cash on Delivery
- Wallet (commission balance)
- Transaction recording with unique references
- Order confirmation flow

### MLM (Multi-Level Marketing)
- 3-level commission structure: 10% / 5% / 2%
- Sponsor referral code system
- Network tree visualization
- Automatic commission calculation on orders
- Commission status tracking (pending → approved → paid)

---

## Database Schema

### Tables (10)
1. **users** — Customer, Partner, Admin accounts
2. **categories** — Product categories (hierarchical)
3. **products** — Product catalog
4. **carts** — User shopping carts
5. **cart_items** — Cart line items
6. **addresses** — Shipping addresses
7. **orders** — Customer orders
8. **order_items** — Order line items
9. **transactions** — Payment transaction records
10. **mlm_commissions** — MLM commission records
11. **wishlists** — User product wishlists

---

## Project Structure
```
Oriflame/
├── app.py                # Main Flask application (all routes)
├── models.py             # SQLAlchemy database models
├── config.py             # Configuration settings
├── requirements.txt      # Python dependencies
├── requirements.md       # This file
├── database/
│   └── oriflame.db       # SQLite database (auto-created)
├── static/
│   ├── css/
│   │   ├── main.css      # Design system & global styles
│   │   └── admin.css     # Admin panel dark theme
│   ├── js/
│   │   ├── main.js       # Navigation, carousel, animations
│   │   ├── cart.js       # Cart operations (AJAX)
│   │   ├── checkout.js   # Checkout & payment
│   │   ├── admin.js      # Admin CRUD operations
│   │   └── mlm.js        # MLM network visualization
│   └── images/
│       └── products/     # Product images
└── templates/
    ├── base.html          # Base template (nav + footer)
    ├── index.html         # Homepage
    ├── products.html      # Product listing
    ├── product_detail.html
    ├── cart.html
    ├── checkout.html
    ├── login.html
    ├── register.html
    ├── dashboard.html
    ├── orders.html
    ├── mlm_network.html
    ├── join.html
    └── admin/
        ├── admin_base.html
        ├── dashboard.html
        ├── products.html
        ├── orders.html
        ├── users.html
        └── mlm.html
```

---

## Security Notes
- Passwords are hashed using Werkzeug's `generate_password_hash`
- Admin panel uses a hidden URL prefix and role-based access control
- Admin routes return 404 (not 403) to hide existence from unauthorized users
- CSRF protection via Flask-WTF
- SQL injection prevented by SQLAlchemy ORM

---

## API Endpoints

### Public
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Homepage |
| GET | `/products` | Product listing |
| GET | `/products/<slug>` | Product detail |
| GET | `/category/<slug>` | Category products |
| GET | `/join` | Business opportunity |

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/login` | User login |
| GET/POST | `/register` | User registration |
| GET | `/logout` | User logout |

### Cart (AJAX)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/cart/add` | Add product to cart |
| GET | `/cart/items` | Get cart items (JSON) |
| POST | `/cart/update` | Update item quantity |
| POST | `/cart/remove` | Remove item from cart |

### Checkout
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/checkout` | Checkout process |
| POST | `/payment/process` | Process payment |

### User Dashboard
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dashboard` | User dashboard |
| GET | `/orders` | Order history |
| GET | `/mlm/network` | MLM network tree |

### Admin (Hidden)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/oriflame-admin-panel-x9k2/` | Admin dashboard |
| GET/POST | `/oriflame-admin-panel-x9k2/products` | Manage products |
| GET | `/oriflame-admin-panel-x9k2/orders` | Manage orders |
| GET | `/oriflame-admin-panel-x9k2/users` | Manage users |
| GET | `/oriflame-admin-panel-x9k2/mlm` | MLM overview |
