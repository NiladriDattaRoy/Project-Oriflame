import sys
import os
sys.path.append(os.getcwd())
from config import Config
import razorpay

key_id = Config.RAZORPAY_KEY_ID
key_secret = Config.RAZORPAY_KEY_SECRET

print(f"Key ID: {repr(key_id)}")
print(f"Key Secret: {repr(key_secret)}")

try:
    # Explicitly strip whitespace just in case
    client = razorpay.Client(auth=(key_id.strip(), key_secret.strip()))
    order = client.order.create({
        'amount': 100,
        'currency': 'INR',
        'receipt': 'TEST1234'
    })
    print("Success!", order)
except Exception as e:
    print(f"ERROR: {e}")
