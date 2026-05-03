import requests
from bs4 import BeautifulSoup
import sys
import re

session = requests.Session()
login_url = "https://project-oriflame-3.onrender.com/login"
r = session.post(login_url, data={"email": "admin@oriflame.com", "password": "admin123"})
if r.status_code != 200:
    print("Login failed")
    sys.exit(1)

admin_url = "https://project-oriflame-3.onrender.com/oriflame-admin-panel-x9k2/products"
r = session.get(admin_url)
soup = BeautifulSoup(r.text, 'html.parser')

product_id = None
for td in soup.find_all('td'):
    if td.text and '46918' in td.text.strip():
        tr = td.find_parent('tr')
        if not tr: continue
        btns = tr.find_all('button')
        for btn in btns:
            onclick = btn.get('onclick', '')
            m = re.search(r'populateFormFromData\((\d+)\)', onclick)
            if m:
                product_id = m.group(1)
                break
        if product_id:
            break

print(f"Found product ID: {product_id}")

get_url = f"https://project-oriflame-3.onrender.com/oriflame-admin-panel-x9k2/get_product/{product_id}"
r = session.get(get_url)
data = r.json()

# Prepare payload for VARIANT
payload = {
    'id': data.get('id', ''),
    'name': data.get('name', '') + ' Variant', # Prevent slug conflict bug by changing name slightly
    'code': data.get('code', ''),
    'price': data.get('price', ''),
    'mrp': data.get('mrp', ''),
    'category_id': data.get('category_id', ''),
    'stock': data.get('stock', ''),
    'brand': data.get('brand', ''),
    'weight': data.get('weight', ''),
    'shade_name': data.get('shadeName', ''),
    'shade_color': '46918',  # UPDATED VALUE
    'shade_color_2': data.get('shadeColor2', ''),
    'parent_id': data.get('parent_id') or '',
    'short_description': data.get('shortDescription', ''),
    'description': data.get('description', ''),
    'how_to_use': data.get('howToUse', ''),
    'ingredients': data.get('ingredients', ''),
}

if data.get('isNew') in [True, 'True', 'true']: payload['is_new'] = 'True'
if data.get('isBestseller') in [True, 'True', 'true']: payload['is_bestseller'] = 'True'

save_url = f"https://project-oriflame-3.onrender.com/oriflame-admin-panel-x9k2/products/{product_id}"
r = session.post(save_url, data=payload)
try:
    print(r.json())
except:
    print(r.text)
