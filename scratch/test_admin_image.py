import requests
import io

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
    
    # 2. Add product with file
    add_url = "https://project-oriflame-3.onrender.com/oriflame-admin-panel-x9k2/products"
    product_data = {
        "name": "Test Product With Image",
        "code": "TESTIMG123",
        "price": "100.0",
        "mrp": "150.0",
        "stock": "50",
    }
    
    # Create a dummy file in memory
    dummy_file = io.BytesIO(b"dummy image data")
    files = {
        'product_images': ('test_image.png', dummy_file, 'image/png')
    }
    
    print("Adding product with image...")
    res_add = session.post(add_url, data=product_data, files=files)
    print(f"Response Code: {res_add.status_code}")
    print(f"Response Text: {res_add.text}")
