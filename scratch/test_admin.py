import requests

session = requests.Session()

# 1. Login
login_url = "https://project-oriflame-3.onrender.com/login"
login_data = {
    "email": "admin@oriflame.com",
    "password": "admin123"
}

print("Attempting to login...")
res = session.post(login_url, data=login_data)
if res.status_code != 200:
    print(f"Login failed: {res.status_code}")
else:
    print("Login successful. Checking cookies...")
    print(session.cookies)
    
    # 2. Add product
    add_url = "https://project-oriflame-3.onrender.com/oriflame-admin-panel-x9k2/products"
    product_data = {
        "name": "Test Product Antigravity",
        "code": "TEST12345",
        "price": "100.0",
        "mrp": "150.0",
        "category_id": "",
        "stock": "50",
        "brand": "Oriflame",
        "description": "Test product description"
    }
    
    print("Adding product...")
    # using data=product_data makes it a form submission
    res_add = session.post(add_url, data=product_data)
    print(f"Response Code: {res_add.status_code}")
    print(f"Response Text: {res_add.text}")
