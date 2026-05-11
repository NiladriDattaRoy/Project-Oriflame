import requests
import bs4

# Check key pages on live site for any 500 errors or obvious issues
pages = [
    'https://project-oriflame-3.onrender.com/',
    'https://project-oriflame-3.onrender.com/products',
    'https://project-oriflame-3.onrender.com/products?filter=bestsellers',
    'https://project-oriflame-3.onrender.com/products?filter=new',
    'https://project-oriflame-3.onrender.com/category/makeup',
    'https://project-oriflame-3.onrender.com/category/skincare',
    'https://project-oriflame-3.onrender.com/login',
    'https://project-oriflame-3.onrender.com/contact',
    'https://project-oriflame-3.onrender.com/catalogue',
    'https://project-oriflame-3.onrender.com/blog',
    'https://project-oriflame-3.onrender.com/join',
    'https://project-oriflame-3.onrender.com/wishlist',
    'https://project-oriflame-3.onrender.com/cart',
    'https://project-oriflame-3.onrender.com/dashboard',
    'https://project-oriflame-3.onrender.com/checkout',
]

print("=== LIVE SITE PAGE SCAN ===")
for url in pages:
    try:
        r = requests.get(url, timeout=15, allow_redirects=True)
        soup = bs4.BeautifulSoup(r.text, 'html.parser')
        title = soup.find('title')
        title_text = title.text[:60] if title else 'No title'
        path = url.replace('https://project-oriflame-3.onrender.com', '') or '/'
        status = 'OK' if r.status_code == 200 else 'FAIL'
        print(f'[{status}] {r.status_code} {path:<35} | {title_text}')
    except Exception as e:
        print(f'[ERR] {url} - {e}')

# Also check a couple of product pages
print()
print("=== PRODUCT PAGES ===")
prod_pages = [
    'https://project-oriflame-3.onrender.com/products/giordani-gold-fabulous-beauty-face-eyes-palette',
    'https://project-oriflame-3.onrender.com/products/the-one-smart-sync-lipstick',
    'https://project-oriflame-3.onrender.com/products/venture-power-eau-de-toilette-',
    'https://project-oriflame-3.onrender.com/products/amber-elixir-eau-de-parfum',
]
for url in prod_pages:
    try:
        r = requests.get(url, timeout=15)
        soup = bs4.BeautifulSoup(r.text, 'html.parser')
        title = soup.find('title')
        title_text = title.text[:50] if title else 'No title'
        path = url.split('/products/')[-1]
        status = 'OK' if r.status_code == 200 else 'FAIL'
        print(f'[{status}] {r.status_code} /products/{path[:30]:<35} | {title_text}')
    except Exception as e:
        print(f'[ERR] {url} - {e}')

# Check admin
print()
print("=== ADMIN PANEL ===")
admin_pages = [
    'https://project-oriflame-3.onrender.com/oriflame-admin-panel-x9k2/',
    'https://project-oriflame-3.onrender.com/oriflame-admin-panel-x9k2/products',
    'https://project-oriflame-3.onrender.com/oriflame-admin-panel-x9k2/orders',
]
for url in admin_pages:
    try:
        r = requests.get(url, timeout=15, allow_redirects=True)
        path = url.replace('https://project-oriflame-3.onrender.com', '')
        # Admin should redirect to login if not authenticated
        final_url = r.url
        status = 'REDIRECT_OK' if '/login' in final_url else ('OK' if r.status_code == 200 else 'FAIL')
        print(f'[{status}] {r.status_code} {path:<45} | Redirected to: {final_url[-30:] if "/login" in final_url else ""}')
    except Exception as e:
        print(f'[ERR] {url} - {e}')
