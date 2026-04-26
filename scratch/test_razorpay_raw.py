import requests
import json

key_id = 'rzp_live_SiC7yQ6wCHXpfb'
key_secret = 'hdAOiUwITZ4KgLsI0Nb6'

auth = (key_id, key_secret)
data = {"amount": 100, "currency": "INR"}

try:
    response = requests.post('https://api.razorpay.com/v1/orders', auth=auth, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
