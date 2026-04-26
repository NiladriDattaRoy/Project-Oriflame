import sys
import os
sys.path.append(os.getcwd())
from config import Config
import razorpay

print(f"Key ID: {Config.RAZORPAY_KEY_ID}")
print(f"Key Secret: {Config.RAZORPAY_KEY_SECRET}")

try:
    client = razorpay.Client(auth=(Config.RAZORPAY_KEY_ID, Config.RAZORPAY_KEY_SECRET))
    order = client.order.create({
        'amount': 100,
        'currency': 'INR',
        'receipt': 'TEST1234',
        'payment_capture': '1'
    })
    print(order)
except Exception as e:
    print(f"ERROR: {e}")
