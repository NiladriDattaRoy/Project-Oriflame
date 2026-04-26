import requests
import uuid

email = f"test{uuid.uuid4().hex[:6]}@oriflame.com"

s = requests.Session()
# Register new user to ensure logged in
res = s.post('http://127.0.0.1:5000/register', data={
    'email': email,
    'password': 'password123',
    'confirm_password': 'password123',
    'first_name': 'Test',
    'last_name': '500',
    'phone': '1234567890',
    'role': 'customer'
})
print("Register response URL:", res.url)

# Add item
res = s.post('http://127.0.0.1:5000/cart/add', json={'product_id': 1, 'quantity': 1})
print("Add cart response:", res.json())

# POST checkout
res = s.post('http://127.0.0.1:5000/checkout', data={
    'payment_method': 'cod',
    'shipping_name': 'Test User',
    'shipping_phone': '1234567890',
    'shipping_address': '123 Test St',
    'shipping_city': 'Test City',
    'shipping_state': 'Test State',
    'shipping_pincode': '123456'
})

print(f"Checkout Status Code: {res.status_code}")
try:
    print(res.json())
except:
    print("HTML Response text (first 500 chars):")
    print(res.text[:500])

